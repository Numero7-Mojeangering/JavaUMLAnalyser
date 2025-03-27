import os
from plantuml import PlantUML

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

# Example usage:
if __name__ == "__main__":
    # Define your PlantUML code
    plantuml_code = """
    @startuml
    Alice -> Bob: Authentication Request
    Bob -> Alice: Authentication Response
    @enduml
    """

    # Create an instance of PlantUMLDiagram
    diagram = PlantUMLDiagram(plantuml_code=plantuml_code, output_file='output/diagram.png')

    # Generate the diagram
    diagram.generate_diagram()

