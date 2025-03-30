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


class JavaElement:
    """Represents a generic Java element (class, interface, enum, primitive)."""
    
    elements: Dict[str, 'JavaElement'] = {}  # Tracks all Java elements by their fully qualified name (FQN)

    def __init__(self, name: str, package: 'JavaPackage', visibility: Optional['JavaVisibility'] = None):
        """
        :param name: The name of the Java element.
        :param package: The JavaPackage object where the element belongs.
        :param visibility: (Optional) The visibility of the element. Defaults to public.
        """
        self.name = name
        self.package = package
        self.relations: list['JavaRelation'] = []
        self.fqn = f"{package.package_name}.{name}"  # Fully Qualified Name (FQN)
        self.visibility = visibility or JavaVisibility(JavaVisibility.PUBLIC)  # Default visibility is public
        JavaElement.elements[self.fqn] = self  # Register element uniquely

    @classmethod
    def add_relation(self, relation: 'JavaRelation'):
        """Adds a relationship to the element."""
        if relation.is_valid():
            self.relations.append(relation)

    @classmethod
    def find(cls, name: str, package: Optional[str] = None) -> Optional['JavaElement']:
        """
        Finds a Java element by name.
        :param name: The name of the Java element.
        :param package: (Optional) The package name to refine the search.
        :return: The found JavaElement or None if not found.
        """
        if package:
            return cls.elements.get(f"{package}.{name}")
        
        # Search for all elements with the given name (without package filtering)
        matches = [elem for fqn, elem in cls.elements.items() if fqn.endswith(f".{name}")]
        return matches[0] if len(matches) == 1 else None  # Return element if unique, else None

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.name}, Package: {self.package.package_name}, Visibility: {self.visibility}"


class JavaRelationType:
    """Represents different types of relationships between Java elements."""

    # Defining constants for different types of relations
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    DEPENDENCY = "dependency"
    ASSOCIATION = "association"
    AGGREGATION = "aggregation"
    COMPOSITION = "composition"
    BIDIRECTIONAL = "bidirectional"
    REFLEXIVE = "reflexive"
    ENUM_USAGE = "enum_usage"

    @classmethod
    def is_valid_relation(cls, relation_type: str) -> bool:
        """Checks if the provided relation type is valid."""
        return relation_type in {
            cls.EXTENDS, cls.IMPLEMENTS, cls.DEPENDENCY, cls.ASSOCIATION,
            cls.AGGREGATION, cls.COMPOSITION, cls.BIDIRECTIONAL, cls.REFLEXIVE, cls.ENUM_USAGE
        }

    @classmethod
    def get_all_relation_types(cls):
        """Returns a list of all valid relation types."""
        return [
            cls.EXTENDS, cls.IMPLEMENTS, cls.DEPENDENCY, cls.ASSOCIATION,
            cls.AGGREGATION, cls.COMPOSITION, cls.BIDIRECTIONAL, cls.REFLEXIVE, cls.ENUM_USAGE
        ]
    
    @classmethod
    def get_uml_symbol(cls, relation_type: str) -> str:
        """Returns the appropriate PlantUML symbol for the given relation type."""
        relation_symbols = {
            cls.EXTENDS: "<|--",
            cls.IMPLEMENTS: "<|..",
            cls.DEPENDENCY: "..>",
            cls.ASSOCIATION: "--",
            cls.AGGREGATION: "o--",
            cls.COMPOSITION: "*--",
            cls.BIDIRECTIONAL: "<-->",
            cls.REFLEXIVE: "--",
            cls.ENUM_USAGE: "..|>"
        }
        return relation_symbols.get(relation_type, "--")  # Default to simple association if type is not found


class JavaRelation:
    """Represents a relationship between two Java elements."""
    
    # Class-level list to store all created relations
    all_relations: List['JavaRelation'] = []

    def __init__(self, source: JavaElement, target: JavaElement, relation_type: str):
        """
        :param source: The source Java element (class, interface, enum, etc.).
        :param target: The target Java element (class, interface, enum, etc.).
        :param relation_type: The type of relationship.
        """
        self.source = source
        self.target = target
        self.relation_type = relation_type

        # Add the created relation to the class-level list
        JavaRelation.all_relations.append(self)

    def __str__(self) -> str:
        return f"{self.source.fqn} {self._get_uml_symbol()} {self.target.fqn}"

    def is_valid(self) -> bool:
        """Checks if the relationship is valid (both source and target exist)."""
        return isinstance(self.source, JavaElement) and isinstance(self.target, JavaElement)

    @classmethod
    def get_all_relations(cls) -> List['JavaRelation']:
        """Returns all created relations."""
        return cls.all_relations


class JavaVisibility:
    """Represents the visibility of a Java element."""
    
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    PACKAGE = "package"
    
    def __init__(self, visibility: str = PUBLIC):
        """
        :param visibility: The visibility level
        """
        if visibility not in {self.PUBLIC, self.PRIVATE, self.PROTECTED, self.PACKAGE}:
            raise ValueError(f"Invalid visibility: {visibility}")
        self.visibility = visibility
    
    def __str__(self) -> str:
        """Returns the visibility level as a string."""
        return self.visibility
    
    def is_public(self) -> bool:
        """Checks if the visibility is public."""
        return self.visibility == self.PUBLIC
    
    def is_private(self) -> bool:
        """Checks if the visibility is private."""
        return self.visibility == self.PRIVATE
    
    def is_protected(self) -> bool:
        """Checks if the visibility is protected."""
        return self.visibility == self.PROTECTED
    
    def is_package(self) -> bool:
        """Checks if the visibility is package."""
        return self.visibility == self.PACKAGE


class JavaMethod:
    """Represents a method in a Java class."""

    def __init__(self, name: str, visibility: 'JavaVisibility', return_type: 'JavaType', parameters: List['JavaType']):
        """
        :param name: The name of the method.
        :param visibility: The visibility of the method (JavaVisibility).
        :param return_type: The return type of the method (JavaType).
        :param parameters: List of parameter types for the method (List of JavaType).
        """
        self.name = name
        self.visibility = visibility
        self.return_type = return_type
        self.parameters = parameters

    def __str__(self) -> str:
        """String representation of the Java method."""
        params = ", ".join(str(param) for param in self.parameters)
        return f"{self.visibility} {self.return_type} {self.name}({params})"


class JavaAttribute:
    """Represents a Java attribute (field) in a class."""
    
    def __init__(self, name: str, attribute_type: str, visibility: JavaVisibility, 
                 is_static: bool = False, is_final: bool = False, 
                 is_transient: bool = False, is_volatile: bool = False) -> None:
        """
        :param name: The name of the attribute (field).
        :param attribute_type: The type of the attribute (e.g., int, String).
        :param visibility: The visibility of the attribute (JavaVisibility).
        :param is_static: Whether the attribute is static.
        :param is_final: Whether the attribute is final (constant).
        :param is_transient: Whether the attribute is transient (not serialized).
        :param is_volatile: Whether the attribute is volatile (for thread safety).
        """
        self.name = name
        self.attribute_type = attribute_type
        self.visibility = visibility  # Instance of JavaVisibility
        self.is_static = is_static
        self.is_final = is_final
        self.is_transient = is_transient
        self.is_volatile = is_volatile

    def __str__(self) -> str:
        """Returns a string representation of the Java attribute."""
        modifiers = []
        
        # Add visibility modifier
        modifiers.append(str(self.visibility))
        
        # Add static, final, transient, volatile modifiers if applicable
        if self.is_static:
            modifiers.append("static")
        if self.is_final:
            modifiers.append("final")
        if self.is_transient:
            modifiers.append("transient")
        if self.is_volatile:
            modifiers.append("volatile")
        
        # Join modifiers with spaces and return the full attribute declaration
        modifier_str = " ".join(modifiers)
        return f"{modifier_str} {self.attribute_type} {self.name}"

class JavaType:
    """Represents a Java type, which could be a primitive type or a Java class."""
    
    PRIMITIVE_TYPES = {"int", "boolean", "char", "byte", "short", "long", "float", "double", "void"}

    def __init__(self, java_class: Optional['JavaClass'] = None, primitive_type: Optional[str] = None):
        """
        :param java_class: The JavaClass object if the type is a class (optional).
        :param primitive_type: The primitive type name (e.g., "int") if it's a primitive (optional).
        """
        if java_class:
            self.java_class = java_class  # Store the JavaClass if it's a class type
            self.primitive_type = None
            self.is_primitive = False
        elif primitive_type and primitive_type in self.PRIMITIVE_TYPES:
            self.java_class = None
            self.primitive_type = primitive_type  # Store the primitive type
            self.is_primitive = True
        else:
            raise ValueError("Must provide either a valid Java class or a primitive type.")

    def get_type(self):
        """Returns the type of the Java type, either class or primitive."""
        if self.is_primitive:
            return self.primitive_type
        elif self.java_class:
            return self.java_class
        else:
            return None

    def __str__(self) -> str:
        """Returns the string representation of the Java type."""
        if self.is_primitive:
            return self.primitive_type  # Return primitive type as is (e.g., "int")
        elif self.java_class:
            return f"{self.java_class.package.package_name}.{self.java_class.name}"  # Fully qualified class name
        return ""
    
    def is_class(self) -> bool:
        """Returns True if the type is a class."""
        return not self.is_primitive
    
    def is_primitive_type(self) -> bool:
        """Returns True if the type is primitive."""
        return self.is_primitive


class JavaClass(JavaElement):
    """Represents a Java class, inheriting from JavaElement, and tracks its relationships with other Java elements."""
    
    def __init__(self, name: str, package: 'JavaPackage', attributes: Dict[str, str], methods: List['JavaMethod'],
                 extends: Optional['JavaClass'] = None, interfaces: Optional[List['JavaInterface']] = None):
        """
        :param name: The name of the class.
        :param package: The package where the class belongs.
        :param attributes: Dictionary of attributes (name, visibility).
        :param methods: List of JavaMethod objects associated with this class.
        :param extends: The class this class extends, if any (JavaClass object).
        :param interfaces: A list of JavaInterface objects associated with this class.
        :param relations: A list of relationships (JavaRelation objects) associated with this class.
        """
        super().__init__(name, package)
        self.attributes = attributes  # Attributes of the class
        self.methods = methods  # List of JavaMethod instances representing methods
        self.extends = extends  # JavaClass object that this class extends (or None if it does not extend anything)
        self.interfaces = interfaces or []  # List of JavaInterface instances associated with this class
    
    def __str__(self) -> str:
        extends_name = self.extends.name if self.extends else "None"
        return f"Class: {self.name}, Package: {self.package}, Extends: {extends_name}, Relations: {len(self.relations)}, Interfaces: {len(self.interfaces)}"


class JavaInterface(JavaElement):
    """Represents a Java Interface."""
    def __init__(self, name: str, package: 'JavaPackage', methods: list[JavaMethod]) -> None:
        super().__init__(name, package)
        self.methods = methods  # Dictionary of methods (name, visibility, return type, parameters)

    def __str__(self) -> str:
        return f"Interface: {self.name}, Package: {self.package}"

class JavaEnum(JavaElement):
    """Represents a Java Enum."""
    def __init__(self, name: str, package: 'JavaPackage', constants: List[str]) -> None:
        super().__init__(name, package)
        self.constants = constants  # List of enum constants

    def __str__(self) -> str:
        return f"Enum: {self.name}, Package: {self.package}, Constants: {', '.join(self.constants)}"

class JavaPackage:
    # Class-level dictionary to store all created packages
    packages: Dict[str, 'JavaPackage'] = {}

    def __init__(self, package_name: str):
        self.package_name = package_name
        self.classes: list['JavaClass'] = []
        self.interfaces: list['JavaInterface'] = []
        self.enums: list['JavaEnum'] = []
        # Register the package by its name
        JavaPackage.packages[package_name] = self

    def add_class(self, java_class: 'JavaClass'):
        """Adds a JavaClass to the package."""
        self.classes.append(java_class)
    
    def add_interface(self, java_interface: 'JavaInterface'):
        """Adds a JavaInterface to the package."""
        self.interfaces.append(java_interface)

    def add_enum(self, java_enum: 'JavaEnum'):
        """Adds a JavaEnum to the package."""
        self.enums.append(java_enum)

    @classmethod
    def find(cls, package_name: str) -> Optional['JavaPackage']:
        """
        Finds a JavaPackage by name.
        :param package_name: The name of the Java package.
        :return: The found JavaPackage instance or None if not found.
        """
        return cls.packages.get(package_name)

    def __str__(self) -> str:
        """String representation of the package."""
        return f"Package: {self.package_name}, Classes: {len(self.classes)}, Interfaces: {len(self.interfaces)}, Enums: {len(self.enums)}"



class JavaProjectParser:
    FILTER_RELATION_SHIPS = True

    def __init__(self, project_path: str):
        self.project_path = project_path

    def parse(self) -> None:
        # Discover classes first
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".java"):
                    self._discover_java_elements(os.path.join(root, file))
        
        # Then extract relationships for the discovered classes
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".java"):
                    self._extract_relationships_from_file(os.path.join(root, file))

    def _discover_java_elements(self, file_path: str) -> None:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                tree = javalang.parse.parse(file.read())
                package_name = self._extract_package(tree)
                # Create or get the package
                package = JavaPackage.find(package_name) or JavaPackage(package_name)

                for _, node in tree:
                    # Check for interface declarations
                    if isinstance(node, javalang.tree.InterfaceDeclaration):
                        methods = self._extract_members(node)
                        java_interface = JavaInterface(node.name, package, methods)
                        package.add_interface(java_interface)

                    # Check for class declarations
                    if isinstance(node, javalang.tree.ClassDeclaration):
                        attributes, methods = self._extract_members(node)
                        extends = self._extract_extends(node)
                        interfaces = self._extract_implements(node)

                        java_class = JavaClass(node.name, package, attributes, methods, extends, interfaces)
                        package.add_class(java_class)

                    # Check for enum declarations
                    if isinstance(node, javalang.tree.EnumDeclaration):
                        constants = [const.name for const in node.constants]
                        java_enum = JavaEnum(node.name, package, constants)
                        package.add_enum(java_enum)

        except (javalang.parser.JavaSyntaxError, FileNotFoundError) as e:
            logging.error(f"Failed to parse {file_path}: {e}")

    def _extract_relationships_from_file(self, file_path: str) -> None:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                tree = javalang.parse.parse(file.read())
                
                for _, node in tree:
                    if isinstance(node, javalang.tree.ClassDeclaration):
                        # Find the Java class for this class declaration
                        package_name = self._extract_package(tree)  # Extract the package name
                        package = JavaPackage.find(package_name)  # Get the package object
                        
                        # Ensure the package exists
                        if package:
                            java_class = next((cls for cls in package.classes if cls.name == node.name), None)
                            
                            if java_class:
                                # Extract relationships for the class
                                relationships = self._extract_relationships(node)
                                
                                # Assign the relationships to the JavaClass object
                                for relation in relationships:
                                    # Create JavaRelation objects for each relationship and add them
                                    relation_type = relation['type']
                                    target = relation['target']
                                    relation_object = JavaRelation(java_class, target, relation_type)
                                    java_class.add_relation(relation_object)

        except (javalang.parser.JavaSyntaxError, FileNotFoundError) as e:
            logging.error(f"Failed to parse {file_path}: {e}")

    def _extract_relationships(self, class_node: javalang.tree.ClassDeclaration) -> list[JavaRelation]:
        relations: list[JavaRelation]
        
        self._extract_aggregations(class_node, relations)
        self._extract_compositions(class_node, relations)
        self._extract_dependencies(class_node, relations)
        self._extract_inheritance_relationships(class_node, relations)
        self._extract_enums(class_node, relations)
        self._extract_associations(class_node, relations)
        self._extract_reflexive_associations(class_node, relations)
        self._extract_bidirectional_associations(class_node, relations)
        
        if JavaProjectParser.FILTER_RELATION_SHIPS:
            return self.limit_relationships(relations)
        else:
            return relations

    def limit_relationships(self, relationships: list[JavaRelation], 
                        max_relations_per_mate: int = 1, 
                        priority_order: List[str] = None) -> list[JavaRelation]:
        """
        Limit the number of relationships based on priority order.
        Select only a certain number of relationships for each type and respects the priority order.
        """
        if priority_order is None:
            priority_order = [
                JavaRelationType.EXTENDS,
                JavaRelationType.COMPOSITION,
                JavaRelationType.AGGREGATION,
                JavaRelationType.DEPENDENCY,
                JavaRelationType.BIDIRECTIONAL,
                JavaRelationType.ASSOCIATION,
                JavaRelationType.REFLEXIVE,
                JavaRelationType.ENUM_USAGE
            ]

        # Prepare a dictionary to store selected relationships
        selected_relationships: list[JavaRelation] = []

        # This dictionary will track how many relationships each mate has across all types
        mate_relationship_count = {}

        # Process each relationship type in priority order
        for relation_type in priority_order:
            # Get the relationship list for this type
            relation_list = [relationship for relationship in relationships if relationship.relation_type == relation_type]
            
            # Process each relationship for this type
            for relationship in relation_list:
                mate_class = relationship.target.fqn  # The class related to the current class
                
                if mate_class not in mate_relationship_count:
                    mate_relationship_count[mate_class] = 0  # Initialize count if not already set

                # If the mate still has space for more relationships, and it has not yet reached the max limit
                if mate_relationship_count[mate_class] < max_relations_per_mate:
                    selected_relationships[relation_type].append(relationship)
                    mate_relationship_count[mate_class] += 1  # Increase the count for this mate

        # Unpack the selected relationships into the return tuple
        return selected_relationships

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
            
            # Method declarations (look for object creation inside methods)
            if isinstance(member, javalang.tree.MethodDeclaration):
                if member.body:  # Ensure body exists and is iterable
                    for statement in member.body:
                        # Look for assignment statements in method body
                        if isinstance(statement, javalang.tree.StatementExpression) and isinstance(statement.expression, javalang.tree.Assignment):
                            value = statement.expression.value
                            if isinstance(value, javalang.tree.ClassCreator):
                                field_type = value.type.name
                                if field_type:
                                    compositions.append(field_type)  # Track object creation for compositions

                        # Check for direct object creation in method body
                        if isinstance(statement, javalang.tree.StatementExpression) and isinstance(statement.expression, javalang.tree.ClassCreator):
                            field_type = statement.expression.type.name
                            if field_type:
                                compositions.append(field_type)  # Track direct object creation for compositions

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
    """Generates PlantUML code from Java class data, grouped by package."""
    def __init__(self, packages: Dict[str, JavaPackage]):
        self.packages = packages

    def generate(self) -> str:
        """Generates PlantUML diagram code for all packages and their classes."""
        uml = ["@startuml"]

        # Generating the package definitions
        for package_name, java_package in self.packages.items():
            uml.append(f"package {package_name} {{")
            
            # Generating the class definitions inside each package
            for cls in java_package.classes:
                uml.append(f" class {cls.name} {{")
                
                # Adding attributes with visibility
                for attr, visibility in cls.attributes.items():
                    uml.append(f"  {visibility} {attr}")
                
                # Adding methods with visibility, return type, and parameters
                for method, signature in cls.methods.items():
                    visibility = signature.get("visibility", "+")  # Default to public if no visibility
                    return_type = signature.get("return_type", "void")
                    parameters = ", ".join(signature.get("parameters", []))
                    uml.append(f"  {visibility} {return_type} {method}({parameters})")
                
                uml.append(" }")  # End class definition
            
            # Generating the interface definitions inside each package
            for iface in java_package.interfaces:
                uml.append(f" interface {iface.name} {{")
                
                # Adding methods with visibility, return type, and parameters for interfaces
                for method, signature in iface.methods.items():
                    visibility = signature.get("visibility", "+")  # Default to public if no visibility
                    return_type = signature.get("return_type", "void")
                    parameters = ", ".join(signature.get("parameters", []))
                    uml.append(f"  {visibility} {return_type} {method}({parameters})")
                
                uml.append(" }")  # End interface definition

            # Generating the enum definitions inside each package
            for enum in java_package.enums:
                uml.append(f" enum {enum.name} {{")
                
                # Adding enum constants
                for constant in enum.constants:
                    uml.append(f"  {constant}")
                
                uml.append(" }")  # End enum definition

            uml.append(" }")  # End package definition

        # Fix to prevent duplicated relations.
        relations: set[str] = set()

        def add_relation(relation: str):
            if relation not in relations:
                uml.append(relation)
                relations.add(relation)

        # Generating relationships
        for java_package in self.packages.values():
            for cls in java_package.classes:
                if cls.extends:
                    add_relation(f"{cls.extends} <|-- {cls.name}")
                for impl in cls.implements:
                    add_relation(f"{impl} <|.. {cls.name}")
                for dep in cls.dependencies:
                    add_relation(f"{cls.name} ..> {dep}")
                for agg in cls.aggregations:
                    add_relation(f"{cls.name} o-- {agg}")
                for comp in cls.compositions:
                    add_relation(f"{cls.name} *-- {comp}")
                for assoc in cls.associations:
                    add_relation(f"{cls.name} -- {assoc}")
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

    generator = PlantUMLGenerator(parser.packages)
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