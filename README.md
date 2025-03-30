# fusion2urdf

This project is a Fusion 360 to URDF exporter, originally forked from [syuntoku14](https://github.com/syuntoku14/fusion2urdf) and later enhanced by [SpaceMaster85](https://github.com/SpaceMaster85/fusion2urdf). The tool converts Fusion 360 designs to URDF format for use in ROS simulations.

## Major Updates

### 2025/03/30: Precision and Performance Improvements
* **Enhanced numerical precision**:
  - Improved handling of small inertia values to prevent truncation to zero
  - Added scientific notation formatting for very small values (<1e-10)
  - Better preservation of floating-point precision throughout calculations
* **Code improvements**:
  - Refactored core functions for better maintainability
  - Updated file copy logic to use modern `shutil` methods
  - Improved timestamp handling in generated files

### 2021/10/13: Version 1.2
* Added robust color and material detection
* Implemented ROS 2 launchfile generator
* Added dialog popup to choose between ROS 1 and ROS 2

### 2021/03/09: Version 1.1
* Fixed Fusion API compatibility issues

### 2021/01/23: Version 1.0
* Added support for nested components
* Light bulb toggle for export selection
* Improved joint coordinate calculations
* Color detection and material assignment
* Temporary file operations (no design modifications)
* Example Fusion 360 files added

## Key Features

* **Precision Handling**:
  - Accurate preservation of small mass and inertia values
  - Scientific notation for very small numbers
  - Proper unit conversions (mm to m for lengths, kg/mm² to kg/m² for inertia)

* **Enhanced Export**:
  - Generates complete ROS package structure
  - Supports both ROS 1 and ROS 2
  - Includes materials, colors, and visual properties
  - Automatic STL generation with proper scaling

* **Improved Workflow**:
  - No need for manual STL conversion
  - Self-contained ROS description packages
  - Xacro-based output for flexibility
  - Separate files for materials, transmissions, and Gazebo elements

## Installation

Run the following command in your shell.

##### Windows (In PowerShell)
```powershell
cd <path to fusion2urdf>
Copy-Item ".\URDF_Exporter\" -Destination "${env:APPDATA}\Autodesk\Autodesk Fusion 360\API\Scripts\" -Recurse
```

##### macOS (In bash or zsh)
```bash
cd <path to fusion2urdf>
cp -r ./URDF_Exporter "$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/"
```

## Usage

1. In Fusion 360, ensure your model components are properly organized
2. Set the base component as "base_link"
3. Run the script from ADD-INS menu
4. Choose output directory when prompted
5. The script generates:
   - URDF/XACRO files
   - STL meshes (converted to meters)
   - Complete ROS package structure
   - Launch files for visualization and simulation

## Important Notes

* **Component Organization**:
  - Parent links must be set as Component2 when defining joints
  - Only components with activated light bulbs will be exported
  - Nested components are exported as single STL files

* **Joint Handling**:
  - Supports "Rigid", "Slider", and "Revolute" joint types
  - Joints with deactivated light bulbs are ignored
  - Joint limits are properly handled

* **Simulation**:
  - For Gazebo: `roslaunch <robot_name>_description gazebo.launch`
  - For RViz: `roslaunch <robot_name>_description display.launch`
```