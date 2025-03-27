import json
import os
import javalang
import logging
from typing import List, Dict, Tuple, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class JavaClass:
    def __init__(self, name: str, package: str, attributes: List[str], methods: List[str],
                 extends: Optional[str] = None, implements: Optional[List[str]] = None,
                 associations: Optional[List[str]] = None, dependencies: Optional[List[str]] = None,
                 aggregations: Optional[List[str]] = None, compositions: Optional[List[str]] = None,
                 bidirectional_associations: Optional[List[str]] = None, reflexive_associations: Optional[List[str]] = None,
                 enums: Optional[List[str]] = None):
        self.name = name
        self.package = package
        self.attributes = attributes
        self.methods = methods
        self.extends = extends
        self.implements = implements or []
        self.associations = associations or []
        self.dependencies = dependencies or []
        self.aggregations = aggregations or []
        self.compositions = compositions or []
        self.bidirectional_associations = bidirectional_associations or []
        self.reflexive_associations = reflexive_associations or []
        self.enums = enums or []

class JavaProjectParser:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.classes: Dict[str, JavaClass] = {}

    def parse(self) -> None:
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".java"):
                    self._discover_java_class(os.path.join(root, file))
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".java"):
                    self._extract_relationships_from_file(os.path.join(root, file))

    def _discover_java_class(self, file_path: str) -> None:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                tree = javalang.parse.parse(file.read())
                package = self._extract_package(tree)
                for _, node in tree:
                    if isinstance(node, javalang.tree.ClassDeclaration):
                        attributes, methods = self._extract_members(node)
                        java_class = JavaClass(node.name, package, attributes, methods)
                        self.classes[java_class.name] = java_class
        except (javalang.parser.JavaSyntaxError, FileNotFoundError) as e:
            logging.error(f"Failed to parse {file_path}: {e}")

    def _extract_relationships_from_file(self, file_path: str) -> None:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                tree = javalang.parse.parse(file.read())
                for _, node in tree:
                    if isinstance(node, javalang.tree.ClassDeclaration) and node.name in self.classes:
                        java_class = self.classes[node.name]
                        (java_class.associations, java_class.dependencies, java_class.aggregations, 
                         java_class.compositions, java_class.bidirectional_associations, 
                         java_class.reflexive_associations, java_class.enums) = self._extract_relationships(node)
        except (javalang.parser.JavaSyntaxError, FileNotFoundError) as e:
            logging.error(f"Failed to parse {file_path}: {e}")

    def _extract_package(self, tree: javalang.tree.CompilationUnit) -> str:
        for _, node in tree:
            if isinstance(node, javalang.tree.PackageDeclaration):
                return node.name
        return "default"

    def _extract_members(self, class_node: javalang.tree.ClassDeclaration) -> Tuple[List[str], List[str]]:
        attributes = [declarator.name for member in class_node.body 
                      if isinstance(member, javalang.tree.FieldDeclaration)
                      for declarator in member.declarators]
        methods = [member.name for member in class_node.body 
                   if isinstance(member, javalang.tree.MethodDeclaration)]
        return attributes, methods

    def _extract_relationships(self, class_node: javalang.tree.ClassDeclaration) -> Tuple[List[str], List[str], List[str], List[str], List[str], List[str], List[str]]:
        associations, dependencies, aggregations, compositions, bidirectional_associations, reflexive_associations, enums = [], [], [], [], [], [], []
        for member in class_node.body:
            if isinstance(member, javalang.tree.FieldDeclaration):
                field_type = member.type.name if hasattr(member.type, 'name') else None
                if field_type:
                    if field_type in self.classes:
                        associations.append(field_type)
                    if field_type in {"List", "Set", "Map"} and member.type.arguments:
                        aggregations.append(member.type.arguments[0].type.name)
                    for declarator in member.declarators:
                        if declarator.initializer and isinstance(declarator.initializer, javalang.tree.ClassCreator):
                            compositions.append(field_type)
                    if field_type == class_node.name:
                        reflexive_associations.append(field_type)
                if field_type and field_type.isupper():
                    enums.append(field_type)
            if isinstance(member, javalang.tree.MethodDeclaration):
                for statement in member.body or []:
                    if isinstance(statement, javalang.tree.StatementExpression) and isinstance(statement.expression, javalang.tree.MethodInvocation):
                        dependencies.append(statement.expression.qualifier)
                    if isinstance(statement, javalang.tree.LocalVariableDeclaration):
                        for declarator in statement.declarators:
                            if isinstance(declarator.initializer, javalang.tree.ClassCreator):
                                dependencies.append(declarator.initializer.type.name)
        return associations, dependencies, aggregations, compositions, bidirectional_associations, reflexive_associations, enums


class PlantUMLGenerator:
    """Generates PlantUML code from Java class data."""
    def __init__(self, classes: Dict[str, JavaClass]):
        self.classes = classes

    def generate(self) -> str:
        """Generates PlantUML diagram code."""
        uml = ["@startuml"]

        for cls in self.classes.values():
            uml.append(f"class {cls.name} {{")
            for attr in cls.attributes:
                uml.append(f"  - {attr}")
            for method in cls.methods:
                uml.append(f"  + {method}()")
            uml.append("}")

        # Fix to prevent duplicated relations.
        relations: set[str] = {""}
        def add_relation(relation: str):
            if not relation in relations:
                uml.append(relation)
            relations.add(relation)

        for cls in self.classes.values():
            if cls.extends:
                add_relation(f"{cls.extends} <|-- {cls.name}")
            for impl in cls.implements:
                add_relation(f"{impl} <|.. {cls.name}")
            for assoc in cls.associations:
                add_relation(f"{cls.name} -- {assoc}")
            for dep in cls.dependencies:
                add_relation(f"{cls.name} ..> {dep}")
            for agg in cls.aggregations:
                add_relation(f"{cls.name} o-- {agg}")
            for comp in cls.compositions:
                add_relation(f"{cls.name} *-- {comp}")
            for bidir in cls.bidirectional_associations:
                add_relation(f"{cls.name} <--> {bidir}")
            for reflexive in cls.reflexive_associations:
                add_relation(f"{cls.name} *-- {reflexive}")

        uml.append("@enduml")
        return "\n".join(uml)


class ConfigLoader:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.config = self.load_config()

    def load_config(self):
        """
        Loads the configuration from the provided JSON file.
        """
        try:
            with open(self.config_file_path, "r", encoding="utf-8") as config_file:
                return json.load(config_file)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return {}

    def get_input_folder(self):
        """
        Returns the input folder from the loaded configuration.
        """
        return self.config.get("input_folder", "./")

    def get_output_uml(self):
        """
        Returns the output UML file path from the loaded configuration.
        """
        return self.config.get("output_uml", "project_diagram.puml")


def main() -> None:
    # Load configuration
    config_loader = ConfigLoader("config.json")
    input_folder = config_loader.get_input_folder()
    output_uml = config_loader.get_output_uml()

    project_directory = input_folder
    parser = JavaProjectParser(project_directory)
    parser.parse()

    generator = PlantUMLGenerator(parser.classes)
    plantuml_code = generator.generate()

    output_file = output_uml
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(plantuml_code)
    
    logging.info(f"PlantUML diagram saved to {output_file}")


if __name__ == "__main__":
    main()