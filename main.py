import os
import javalang
import logging
from typing import List, Dict, Tuple, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class JavaClass:
    """Represents a Java class with attributes, methods, and relationships."""
    def __init__(self, name: str, package: str, attributes: List[str], methods: List[str],
                 extends: Optional[str] = None, implements: Optional[List[str]] = None,
                 associations: Optional[List[str]] = None, dependencies: Optional[List[str]] = None,
                 aggregations: Optional[List[str]] = None, compositions: Optional[List[str]] = None,
                 bidirectional_associations: Optional[List[str]] = None, reflexive_associations: Optional[List[str]] = None,
                 static_dependencies: Optional[List[str]] = None, package_friends: Optional[List[str]] = None):
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
        self.static_dependencies = static_dependencies or []
        self.package_friends = package_friends or []
    
    def __str__(self) -> str:
        return (f"Class: {self.name}, Package: {self.package}, "
                f"Extends: {self.extends}, Implements: {self.implements}, "
                f"Associations: {self.associations}, Dependencies: {self.dependencies}, "
                f"Aggregations: {self.aggregations}, Compositions: {self.compositions}, "
                f"Bidirectional Associations: {self.bidirectional_associations}, "
                f"Reflexive Associations: {self.reflexive_associations}, "
                f"Static Dependencies: {self.static_dependencies}, "
                f"Package Friends: {self.package_friends}")

class JavaProjectParser:
    """Parses a Java project to extract class details."""
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.classes: Dict[str, JavaClass] = {}

    def parse(self) -> None:
        """Parses Java files in the given project path."""
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".java"):
                    self._parse_java_file(os.path.join(root, file))

    def _parse_java_file(self, file_path: str) -> None:
        """Parses an individual Java file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                tree = javalang.parse.parse(file.read())
                package = self._extract_package(tree)
                
                for _, node in tree:
                    if isinstance(node, javalang.tree.ClassDeclaration):
                        attributes, methods = self._extract_members(node)
                        extends = node.extends.name if node.extends else None
                        implements = [impl.name for impl in node.implements] if node.implements else []
                        relationships = self._extract_relationships(node, file_path)
                        
                        java_class = JavaClass(node.name, package, attributes, methods, extends, implements, *relationships)
                        self.classes[java_class.name] = java_class
                        logging.info(f"Parsed: {java_class}")
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

    def _extract_relationships(self, class_node: javalang.tree.ClassDeclaration, file_path: str) -> Tuple[List[str], List[str], List[str], List[str], List[str], List[str], List[str], List[str]]:
        associations, dependencies, aggregations, compositions = [], [], [], []
        bidirectional_associations, reflexive_associations, static_dependencies, package_friends = [], [], [], []
        
        for member in class_node.body:
            if isinstance(member, javalang.tree.FieldDeclaration):
                field_type = member.type.name if hasattr(member.type, 'name') else None
                if field_type:
                    associations.append(field_type)
                    if field_type in {"List", "Set", "Map"} and member.type.arguments:
                        aggregations.append(member.type.arguments[0].type.name)
                    if field_type == class_node.name:
                        reflexive_associations.append(field_type)
                
            elif isinstance(member, javalang.tree.MethodDeclaration):
                for param in member.parameters:
                    if hasattr(param.type, 'name'):
                        dependencies.append(param.type.name)
                        if param.type.name == class_node.name:
                            reflexive_associations.append(param.type.name)
                
                # Detect static method calls
                for _, expression in member:
                    if isinstance(expression, javalang.tree.MethodInvocation) and '.' in expression.qualifier:
                        static_dependencies.append(expression.qualifier.split('.')[0])
        
        # Package-private relationships
        class_package = self._extract_package(javalang.parse.parse(open(file_path).read()))
        for other_class in self.classes.values():
            if other_class.package == class_package and other_class.name != class_node.name:
                package_friends.append(other_class.name)
        
        return associations, dependencies, aggregations, compositions, bidirectional_associations, reflexive_associations, static_dependencies, package_friends


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

            if cls.extends:
                uml.append(f"{cls.extends} <|-- {cls.name}")
            for impl in cls.implements:
                uml.append(f"{impl} <|.. {cls.name}")
            for assoc in cls.associations:
                uml.append(f"{cls.name} -- {assoc}")
            for dep in cls.dependencies:
                uml.append(f"{cls.name} ..> {dep}")
            for agg in cls.aggregations:
                uml.append(f"{cls.name} o-- {agg}")
            for comp in cls.compositions:
                uml.append(f"{cls.name} *-- {comp}")
            for bidir in cls.bidirectional_associations:
                uml.append(f"{cls.name} <--> {bidir}")
            for reflexive in cls.reflexive_associations:
                uml.append(f"{cls.name} *-- {reflexive}")

        uml.append("@enduml")
        return "\n".join(uml)


def main() -> None:
    project_directory = "Robot2D_v0_ISOARD_VALENTIN"  # Change this to your Java project path
    parser = JavaProjectParser(project_directory)
    parser.parse()

    generator = PlantUMLGenerator(parser.classes)
    plantuml_code = generator.generate()

    output_file = "JavaUMLGenerator/plantuml_diagram.puml"
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(plantuml_code)
    
    logging.info(f"PlantUML diagram saved to {output_file}")


if __name__ == "__main__":
    main()
