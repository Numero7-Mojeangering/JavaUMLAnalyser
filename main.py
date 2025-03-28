"""
This program extracts class relationships from a Java project and generates a UML diagram using PlantUML.

The process involves parsing Java source files, generating PlantUML code based on the relationships between
classes, and then generating a visual UML diagram from the PlantUML code.

This project was developed with the help of ChatGPT. The solutions provided by ChatGPT were stitched together.

Author: Numero7 Mojeangering (Valentin ISOARD)
"""
import json
import os
import javalang
import logging
from typing import List, Dict, Tuple, Optional
from plantuml import PlantUML

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class JavaClass:
    def __init__(self, name: str, package: str, attributes: Dict[str, str], methods: Dict[str, Dict[str, List[str]]],
                 extends: Optional[str] = None, implements: Optional[List[str]] = None,
                 associations: Optional[List[str]] = None, dependencies: Optional[List[str]] = None,
                 aggregations: Optional[List[str]] = None, compositions: Optional[List[str]] = None,
                 bidirectional_associations: Optional[List[str]] = None, reflexive_associations: Optional[List[str]] = None,
                 enums: Optional[List[str]] = None, external_inheritance: Optional[List[str]] = None):
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
        self.external_inheritance = external_inheritance or []
    

class JavaProjectParser:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.classes: Dict[str, 'JavaClass'] = {}

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
                        extends = self._extract_extends(node)
                        implements = self._extract_implements(node)
                        java_class = JavaClass(node.name, package, attributes, methods, extends, implements)
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
                         java_class.reflexive_associations, java_class.enums, 
                         java_class.external_inheritance) = self._extract_relationships(node)
        except (javalang.parser.JavaSyntaxError, FileNotFoundError) as e:
            logging.error(f"Failed to parse {file_path}: {e}")

    def _extract_relationships(self, class_node: javalang.tree.ClassDeclaration) -> Tuple[List[str], List[str], List[str], List[str], List[str], List[str], List[str], List[str]]:
        associations, dependencies, aggregations, compositions, bidirectional_associations, reflexive_associations, enums, external_inheritance = [], [], [], [], [], [], [], []
        
        self._extract_aggregations(class_node, aggregations)

        self._extract_compositions(class_node, compositions)

        self._extract_dependencies(class_node, dependencies)

        self._extract_inheritance_relationships(class_node, external_inheritance)

        self._extract_enums(class_node, enums)

        self._extract_associations(class_node, associations)

        self._extract_reflexive_associations(class_node, reflexive_associations)

        self._extract_bidirectional_associations(class_node, associations, bidirectional_associations)
        
        return associations, dependencies, aggregations, compositions, bidirectional_associations, reflexive_associations, enums, external_inheritance

    def _extract_package(self, tree: javalang.tree.CompilationUnit) -> str:
        for _, node in tree:
            if isinstance(node, javalang.tree.PackageDeclaration):
                return node.name
        return "default"

    def _extract_members(self, class_node: javalang.tree.ClassDeclaration) -> Tuple[Dict[str, str], Dict[str, Dict[str, List[str]]]]:
        attributes = {declarator.name: self._get_field_type(member) for member in class_node.body
                      if isinstance(member, javalang.tree.FieldDeclaration)
                      for declarator in member.declarators}
        
        methods = {member.name: self._get_method_signature(member) for member in class_node.body 
                   if isinstance(member, javalang.tree.MethodDeclaration)}
        
        return attributes, methods

    def _get_field_type(self, field_decl: javalang.tree.FieldDeclaration) -> str:
        """Extracts the type of the field and visibility (public, private, protected)."""
        visibility = self._get_visibility_from_modifiers(field_decl.modifiers)
        field_type = field_decl.type.name if hasattr(field_decl.type, 'name') else "Unknown"
        return f"{visibility} {field_type}"

    def _get_method_signature(self, method_node: javalang.tree.MethodDeclaration) -> Dict[str, List[str]]:
        """Extracts the method signature, return type, parameters, and visibility."""
        visibility = self._get_visibility_from_modifiers(method_node.modifiers)
        return_type = method_node.return_type.name if hasattr(method_node.return_type, 'name') else "void"
        parameters = [param.type.name if hasattr(param.type, 'name') else "Unknown" for param in method_node.parameters]
        return {
            "visibility": visibility,
            "return_type": return_type,
            "parameters": parameters
        }
    
    def _get_visibility_from_modifiers(self, modifiers: List[str]) -> str:
        """Extracts visibility from method or field modifiers."""
        if "public" in modifiers:
            return "+"
        elif "private" in modifiers:
            return "-"
        elif "protected" in modifiers:
            return "#"
        else:
            return "~"

    def _extract_extends(self, class_node: javalang.tree.ClassDeclaration) -> Optional[str]:
        """ Extracts the parent class the current class extends. """
        if class_node.extends:
            return class_node.extends.name
        return None

    def _extract_implements(self, class_node: javalang.tree.ClassDeclaration) -> List[str]:
        """ Extracts the interfaces the class implements. """
        return [iface.name for iface in class_node.implements] if class_node.implements else []

    def _extract_field_relationships(self, class_node: javalang.tree.ClassDeclaration, associations: List[str], aggregations: List[str], compositions: List[str], reflexive_associations: List[str], enums: List[str]) -> None:
        for member in class_node.body:
            if isinstance(member, javalang.tree.FieldDeclaration):
                field_type = member.type.name if hasattr(member.type, 'name') else None

                if field_type and field_type.strip():
                    # Handle generic collections (e.g., List<SomeType>)
                    if hasattr(member.type, 'arguments') and member.type.arguments:
                        for argument in member.type.arguments:
                            inner_type = argument.type.name if hasattr(argument.type, 'name') else None
                            if inner_type in self.classes:
                                associations.append(inner_type)  # Add inner types as associations
                            if inner_type:
                                aggregations.append(inner_type)  # Track aggregations as well

                    # Check for direct class references (associations)
                    if field_type in self.classes:
                        associations.append(field_type)

                    # Check for compositions if the field is created using an initializer expression
                    for declarator in member.declarators:
                        if declarator.initializer and isinstance(declarator.initializer, javalang.tree.ClassCreator):
                            compositions.append(field_type)

                    # Reflexive association (class referencing itself)
                    if field_type == class_node.name:
                        reflexive_associations.append(field_type)

                    # Check for enums (uppercase field type is a heuristic, but could be improved)
                    if field_type and field_type.isupper():  # Better to explicitly check if field is an enum
                        enums.append(field_type)

    def _extract_constructor_relationships(self, class_node: javalang.tree.ClassDeclaration, compositions: List[str]) -> None:
        for member in class_node.body:
            if isinstance(member, javalang.tree.ConstructorDeclaration):
                for statement in member.body:
                    if isinstance(statement, javalang.tree.StatementExpression) and isinstance(statement.expression, javalang.tree.Assignment):
                        value = statement.expression.value
                        if isinstance(value, javalang.tree.ClassCreator):
                            field_type = value.type.name
                            compositions.append(field_type)  # Track compositions

    def _extract_reflexive_associations(self, class_node: javalang.tree.ClassDeclaration, reflexive_associations: List[str]) -> None:
        # Check field declarations
        for member in class_node.body:
            if isinstance(member, javalang.tree.FieldDeclaration):
                field_type = member.type.name if hasattr(member.type, 'name') else None
                
                # Check if the field's type is the same as the class's name
                if field_type == class_node.name:
                    reflexive_associations.append(field_type)
        
        # Check method declarations for parameters or return types that are the same as the class's name
        for member in class_node.body:
            if isinstance(member, javalang.tree.MethodDeclaration):
                # Check return type
                return_type = member.return_type.name if hasattr(member.return_type, 'name') else None
                if return_type == class_node.name:
                    reflexive_associations.append(class_node.name)
                
                # Check method parameters
                for param in member.parameters:
                    param_type = param.type.name if hasattr(param.type, 'name') else None
                    if param_type == class_node.name:
                        reflexive_associations.append(class_node.name)


    def _extract_compositions(self, class_node: javalang.tree.ClassDeclaration, compositions: List[str]) -> None:
        for member in class_node.body:
            if isinstance(member, javalang.tree.FieldDeclaration):
                # Iterate through all field declarators
                for declarator in member.declarators:
                    if declarator.initializer and isinstance(declarator.initializer, javalang.tree.ClassCreator):
                        # Check if the field is being initialized with a new object
                        field_type = member.type.name if hasattr(member.type, 'name') else None
                        if field_type:
                            compositions.append(field_type)  # Track object creation for compositions

            # Check constructor methods (ConstructorDeclaration in javalang)
            if isinstance(member, javalang.tree.ConstructorDeclaration):
                # Iterate through the constructor's body to find object creation
                for statement in member.body:
                    if isinstance(statement, javalang.tree.StatementExpression) and isinstance(statement.expression, javalang.tree.Assignment):
                        # Check for assignments where the right-hand side is a ClassCreator (object creation)
                        value = statement.expression.value
                        if isinstance(value, javalang.tree.ClassCreator):
                            # Get the type of the created object (e.g., ArrayList)
                            field_type = value.type.name
                            if field_type:
                                compositions.append(field_type)  # Track object creation for compositions

    def _extract_inheritance_relationships(self, class_node: javalang.tree.ClassDeclaration, external_inheritance: List[str]) -> None:
        if class_node.extends:
            external_inheritance.append(class_node.extends.name)
    
    def _extract_enums(self, class_node: javalang.tree.ClassDeclaration, enums: List[str]) -> None:
        # Check all field declarations in the class
        for member in class_node.body:
            if isinstance(member, javalang.tree.FieldDeclaration):
                # Get the field type
                field_type = member.type.name if hasattr(member.type, 'name') else None
                
                # Check if the field is an enum type
                if field_type and field_type.isupper():
                    enums.append(field_type)
            
            # Check for enum declaration within the class itself
            if isinstance(member, javalang.tree.EnumDeclaration):
                enums.append(member.name)

    def _extract_associations(self, class_node: javalang.tree.ClassDeclaration, associations: List[str]) -> None:
        # Iterate over all fields to check for associations
        for member in class_node.body:
            if isinstance(member, javalang.tree.FieldDeclaration):
                # Retrieve the field's type
                field_type = member.type.name if hasattr(member.type, 'name') else None
                if field_type and field_type.strip():
                    # 1. Direct association to another class (excluding the class itself)
                    if field_type in self.classes and field_type != class_node.name:
                        associations.append(field_type)

                    # 2. Handle generic types (collections or parameterized types)
                    if hasattr(member.type, 'arguments') and member.type.arguments:
                        for argument in member.type.arguments:
                            # Extract the inner type of the generic
                            inner_type = argument.type.name
                            # Ensure the inner type is a valid class reference
                            if inner_type in self.classes:
                                associations.append(inner_type)

                    # 3. If the field type is a collection or array of another class
                    elif hasattr(member.type, 'dimensions') and member.type.dimensions:
                        # Check for arrays (e.g., String[] or SomeClass[])
                        array_type = member.type.name
                        if array_type in self.classes and array_type != class_node.name:
                            associations.append(array_type)

                    # 4. Handle intersection types or multiple associations
                    if hasattr(member.type, 'type'):
                        if member.type.type.name != field_type and member.type.type.name in self.classes:
                            associations.append(member.type.type.name)

        # Ensure no duplicate associations are added
        associations[:] = list(set(associations))


        # Check constructor methods (ConstructorDeclaration in javalang)
        for member in class_node.body:
            if isinstance(member, javalang.tree.ConstructorDeclaration):
                # Check the body for object creation (ClassCreator)
                for statement in member.body:
                    if isinstance(statement, javalang.tree.StatementExpression) and isinstance(statement.expression, javalang.tree.Assignment):
                        value = statement.expression.value
                        if isinstance(value, javalang.tree.ClassCreator):
                            field_type = value.type.name
                            if field_type in self.classes and field_type != class_node.name:
                                associations.append(field_type)

        # Check method parameters (MethodDeclaration)
        for member in class_node.body:
            if isinstance(member, javalang.tree.MethodDeclaration):
                for parameter in member.parameters:
                    param_type = parameter.type.name if hasattr(parameter.type, 'name') else None
                    if param_type and param_type != class_node.name:
                        # If the parameter is a reference to another class, it's an association
                        if param_type in self.classes:
                            associations.append(param_type)

    def _extract_aggregations(self, class_node: javalang.tree.ClassDeclaration, aggregations: List[str]) -> None:
        for member in class_node.body:
            if isinstance(member, javalang.tree.FieldDeclaration):
                # Get the field type (not the name)
                field_type = member.type.name if hasattr(member.type, 'name') else None
                
                if field_type:
                    # Check if the field is a collection or array (e.g., List<Something>, Set<Something>, Map<K, V>)
                    if hasattr(member.type, 'arguments') and member.type.arguments:
                        # The type arguments represent the inner types of collections (e.g., List<String>)
                        for argument in member.type.arguments:
                            inner_type = argument.type.name
                            if inner_type:
                                aggregations.append(inner_type)
                    # Check for array types (e.g., MyClass[] or SomeType[])
                    if field_type.endswith("[]"):
                        array_type = field_type[:-2]  # Remove the "[]" part
                        aggregations.append(array_type)

    def _extract_dependencies(self, class_node: javalang.tree.ClassDeclaration, dependencies: List[str]) -> None:
        # Check method declarations for dependencies via method invocations
        for member in class_node.body:
            if isinstance(member, javalang.tree.MethodDeclaration):
                for statement in member.body or []:
                    # Check if the statement is a method invocation with a qualifier (i.e., an object is invoking the method)
                    if isinstance(statement, javalang.tree.StatementExpression) and isinstance(statement.expression, javalang.tree.MethodInvocation):
                        method_invocation = statement.expression
                        if method_invocation.qualifier:  # Qualifier refers to the object or class being invoked
                            qualifier = method_invocation.qualifier
                            qualifier_type = qualifier.type.name if hasattr(qualifier, 'type') else None
                            if qualifier_type and qualifier_type != class_node.name:
                                dependencies.append(qualifier_type)

                    # Check for local variable declarations and the object creation (ClassCreator) inside them
                    if isinstance(statement, javalang.tree.LocalVariableDeclaration):
                        for declarator in statement.declarators:
                            if isinstance(declarator.initializer, javalang.tree.ClassCreator):
                                # Track the dependencies as the class instance is created
                                initializer_type = declarator.initializer.type.name if hasattr(declarator.initializer.type, 'name') else None
                                if initializer_type and initializer_type != class_node.name:
                                    dependencies.append(initializer_type)

    def _extract_bidirectional_associations(self, class_node: javalang.tree.ClassDeclaration, associations: List[str], bidirectional_associations: List[str]) -> None:
        # Iterate over all fields to check for associations
        for member in class_node.body:
            if isinstance(member, javalang.tree.FieldDeclaration):
                field_type = member.type.name if hasattr(member.type, 'name') else None
                if field_type and field_type.strip():
                    # Check if the field type is an association with another class
                    if field_type in self.classes and field_type != class_node.name:
                        # If the associated class also has a reference to this class, it's bidirectional
                        associated_class = self.classes[field_type]
                        if class_node.name in associated_class.associations:
                            # Add both classes to the bidirectional associations
                            if (field_type, class_node.name) not in bidirectional_associations:
                                bidirectional_associations.append((class_node.name, field_type))

        # Check for bidirectional relationships in constructors (object creation involving two related classes)
        for member in class_node.body:
            if isinstance(member, javalang.tree.ConstructorDeclaration):
                for statement in member.body:
                    if isinstance(statement, javalang.tree.StatementExpression) and isinstance(statement.expression, javalang.tree.Assignment):
                        value = statement.expression.value
                        if isinstance(value, javalang.tree.ClassCreator):
                            field_type = value.type.name
                            if field_type in self.classes and field_type != class_node.name:
                                associated_class = self.classes[field_type]
                                if class_node.name in associated_class.associations:
                                    if (class_node.name, field_type) not in bidirectional_associations:
                                        bidirectional_associations.append((class_node.name, field_type))

        # Check for bidirectional associations in method invocations (if one class calls a method on another class)
        for member in class_node.body:
            if isinstance(member, javalang.tree.MethodDeclaration):
                for statement in member.body or []:
                    if isinstance(statement, javalang.tree.StatementExpression) and isinstance(statement.expression, javalang.tree.MethodInvocation):
                        qualifier = statement.expression.qualifier
                        if qualifier and qualifier in self.classes:
                            called_class = self.classes[qualifier]
                            if class_node.name in called_class.associations:
                                if (class_node.name, qualifier) not in bidirectional_associations:
                                    bidirectional_associations.append((class_node.name, qualifier))



class PlantUMLGenerator:
    """Generates PlantUML code from Java class data."""
    def __init__(self, classes: Dict[str, JavaClass]):
        self.classes = classes

    def generate(self) -> str:
        """Generates PlantUML diagram code."""
        uml = ["@startuml"]

        # Generating the class definitions
        for cls in self.classes.values():
            uml.append(f"class {cls.name} {{")
            
            # Adding attributes with visibility
            for attr, visibility in cls.attributes.items():
                uml.append(f" {visibility} {attr}")
            
            # Adding methods with visibility, return type, and parameters
            for method, signature in cls.methods.items():
                visibility = signature.get("visibility", "+")  # Default to public if no visibility
                return_type = signature.get("return_type", "void")
                parameters = ", ".join(signature.get("parameters", []))
                uml.append(f" {visibility} {return_type} {method}({parameters})")
                
            uml.append("}")

        # Fix to prevent duplicated relations.
        relations: set[str] = set()

        def add_relation(relation: str):
            if relation not in relations:
                uml.append(relation)
                relations.add(relation)

        # Generating relationships
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
                add_relation(f"{cls.name} -- {reflexive}")

        uml.append("@enduml")
        return "\n".join(uml)



class PlantUMLDiagram:
    def __init__(self, plantuml_code: str, output_file: str, server_url: str = 'http://www.plantuml.com/plantuml/img/'):
        """
        Initializes the PlantUMLDiagram instance.

        :param plantuml_code: The PlantUML code as a string.
        :param output_file: The desired output file name (e.g., 'diagram.png').
        :param server_url: The URL of the PlantUML server (default is the public server).
        """
        self.plantuml_code = plantuml_code
        self.output_file = output_file
        self.server_url = server_url
        self.plantuml = PlantUML(url=self.server_url)

    def generate_diagram(self):
        """
        Generates the UML diagram by sending the PlantUML code to the server.
        Saves the diagram to the specified output file.
        """
        try:
            # Process the PlantUML code and retrieve the diagram
            diagram_data = self.plantuml.processes(self.plantuml_code)

            # Ensure the output directory exists
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

            # Write the diagram data to the output file
            with open(self.output_file, 'wb') as file:
                file.write(diagram_data)
            print(f"Diagram successfully generated and saved to {self.output_file}")
        except Exception as e:
            print(f"An error occurred while generating the diagram: {e}")

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

    def get_project_folder(self):
        """
        Returns the input folder from the loaded configuration.
        """
        return self.config.get("java_project_folder", "./")

    def get_output_uml_code(self):
        """
        Returns the output UML RAW file path from the loaded configuration.
        """
        return self.config.get("output_uml_code", "project_diagram.puml")
    
    def get_output_uml_diagram(self):
        """
        Returns the output UML PNG file path from the loaded configuration.
        """
        return self.config.get("output_uml_diagram", "project_diagram.png")


def main() -> None:
    # Load configuration
    config_loader = ConfigLoader("config.json")
    project_folder = config_loader.get_project_folder()
    output_uml = config_loader.get_output_uml_code()
    output_diagram = config_loader.get_output_uml_diagram()

    parser = JavaProjectParser(project_folder)
    parser.parse()

    generator = PlantUMLGenerator(parser.classes)
    plantuml_code = generator.generate()

    with open(output_uml, "w", encoding="utf-8") as file:
        file.write(plantuml_code)

    # Create an instance of PlantUMLDiagram
    diagram = PlantUMLDiagram(plantuml_code=plantuml_code, output_file=output_diagram)

    # Generate the diagram
    diagram.generate_diagram()
    
    logging.info(f"PlantUML diagram saved to {output_diagram}")


if __name__ == "__main__":
    main()