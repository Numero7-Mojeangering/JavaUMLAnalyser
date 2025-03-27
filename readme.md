# How to Use the Java Project Parser and PlantUML Diagram Generator

## Overview:
This program extracts class relationships from a Java project and generates a UML diagram using PlantUML. The process involves parsing Java source files, generating PlantUML code based on the relationships between classes, and then generating a visual UML diagram from the PlantUML code.

This project was developed with the help of ChatGPT.
I've stitched together solutions it provided.

## Prerequisites:
1. **Python 3.x**: The program requires Python 3.x to run.
2. **Required Libraries**:
   - `javalang`: For parsing Java source files.
   - `plantuml`: To interface with the PlantUML server.
   - `json`: For loading configuration files.
   - `os`: To handle file and directory creation.
   - `logging`: For logging purposes.

   You can install the required libraries using pip:

   ```bash
   pip install javalang plantuml
   ```

## Step-by-Step Guide:

### 1. Configuration File (`config.json`):
The program uses a configuration file (`config.json`) to define project-specific settings. The configuration file should be structured as follows:

```json
{
  "java_project_folder": "/path/to/your/java/project",
  "output_uml_code": "output.puml",
  "output_uml_diagram": "output.png"
}
```

   - **java_project_folder**: The folder path of your Java project (where your `.java` files are located).
   - **output_uml_code**: The path where the generated PlantUML code will be saved (e.g., `project.puml`).
   - **output_uml_diagram**: The path where the generated UML diagram image will be saved (e.g., `project.png`).

### 2. How to Run the Program:
   - Ensure your Java project folder is correct in the `config.json` file.
   - Run the Python program by executing:

     ```bash
     python your_script_name.py
     ```

   The program will perform the following steps:
   1. Load the configuration from `config.json`.
   2. Parse the Java source files in the specified folder.
   3. Generate the PlantUML code based on the relationships between classes.
   4. Save the generated PlantUML code to a `.puml` file.
   5. Send the PlantUML code to the PlantUML server to generate the diagram.
   6. Save the UML diagram image to the specified output file (e.g., `.png`).

### 3. Output:
   - The program will generate two files:
     - A `.puml` file containing the PlantUML code.
     - A `.png` file containing the UML diagram.

   The program will print a success message to the console once the diagram is generated and saved.

### 4. Logging:
   The program uses the `logging` library to log information and errors. The generated logs will include information about the UML diagram being saved.

## Troubleshooting:
- If you encounter any issues while running the program, check the following:
  - Ensure that the Java source files are located in the correct folder specified in `config.json`.
  - Check the file paths for the output files to ensure they are valid.
  - Review the logs for more information about any errors that occurred.

## Example Output:

```bash
Diagram successfully generated and saved to project_diagram.png
PlantUML diagram saved to project_diagram.png
```
