# Hardware

[English](HardWare.md) | [日本語](HardWare_ja.md)

This document provides information on 3D-printable hardware models and printing guidelines.  
The images show the **recommended print orientation** on the build plate in the slicer.

## Recommended Print Settings (BambuLab P1S)

All parts, except for the motor mounts, can be printed using the common settings.

### 1. Common Settings (All parts except Motor Mounts)

Based on the Bambu Studio standard preset **`0.20mm Standard`** with support enabled.

- **Recommended Material**: PLA
- **Base Preset**: `0.20mm Standard`
- **Supports**:
  - **Enable Support**: ON
  - **Type**: **Tree**
  *(Automatic tree support ensures stable printing even for parts with overhangs)*

### 2. Motor Mount Settings

Uses the Bambu Studio standard preset **`0.20mm Strength`**. Wall loops and infill density are preconfigured for structural strength.

- **Recommended Material**: PETG or ABS (recommended due to motor clamping torque, vibrations, and mechanical stress)
- **Base Preset**: `0.20mm Strength`
- **Supports**:
  - **Enable Support**: ON (Tree support recommended)
  - Using Bambu Lab support filament (e.g., Support for PLA/PETG) makes the interface layer easy to remove and ensures a clean finish.

---

## 3D Printed Parts List

| Part Name              | File                                           |  Qty  | Print Setting (Preset) | Notes                                                       |
| :--------------------- | :--------------------------------------------- | :---: | :--------------------: | :---------------------------------------------------------- |
| **RealSense Mount**    | [RealSenseMounter.stl](./RealSenseMounter.stl) |   1   | 0.20mm Standard (Tree) | No support needed                                           |
| **Camera Holder Jig**  | [CameraAngle.stl](./CameraAngle.stl)           |   2   | 0.20mm Standard (Tree) | No support needed                                           |
| **Motor Mount L**      | [MotorMount_L.stl](./MotorMount_L.stl)         |   1   |  **0.20mm Strength**   | PETG/ABS recommended, support material recommended          |
| **Motor Mount R**      | [MotorMount_R.stl](./MotorMount_R.stl)         |   1   |  **0.20mm Strength**   | PETG/ABS recommended, support material recommended          |
| **Leg**                | [Leg.stl](./Leg.stl)                           |   2   | 0.20mm Standard (Tree) | No support needed                                           |
| **Limit Switch Mount** | [LimitSwitchMount.stl](./LimitSwitchMount.stl) |   1   | 0.20mm Standard (Tree) | No support needed                                           |
| **Pulley Mount A_L**   | [PulleyMountA_L.stl](./PulleyMountA_L.stl)     |   1   | 0.20mm Standard (Tree) | -                                                           |
| **Pulley Mount A_R**   | [PulleyMountA_R.stl](./PulleyMountA_R.stl)     |   1   | 0.20mm Standard (Tree) | -                                                           |
| **Pulley Mount B**     | [PulleyMountB.stl](./PulleyMountB.stl)         |   1   | 0.20mm Standard (Tree) | -                                                           |
| **Pulley Mount C**     | [PulleyMountC.stl](./PulleyMountC.stl)         |   1   | 0.20mm Standard (Tree) | -                                                           |
| **Arm Holder**         | [Arm_Holder.stl](./Arm_Holder.stl)             |   1   | 0.20mm Standard (Tree) | Significant supports, support material strongly recommended |
| **Stopper**            | [Stopper.stl](./Stopper.stl)                   |   2   | 0.20mm Standard (Tree) | No support needed                                           |

---

## Part Details

### Camera

- [RealSense Mount](./RealSenseMounter.stl)
  - Quantity: 1
  - Setting: Common Settings
  ![RealSense Mount](./assets/RealSenseMounter.png)
  
- [Camera Holder Jig](./CameraAngle.stl)
  - Quantity: 2
  - Setting: Common Settings
  ![Camera Holder Jig](./assets/CameraAngle.png)
  
### Main Body

- Motor Mounts
  - [MotorMount_L.stl](./MotorMount_L.stl) (Left: 1)
  - [MotorMount_R.stl](./MotorMount_R.stl) (Right: 1)
  - Setting: **Motor Mount Settings (0.20mm Strength)**
  - Due to mechanical load, we recommend higher infill density or strong filament such as ABS or PETG.
  - Using Bambu Lab support filament helps achieve a clean finish.
  ![Motor Mount](./assets/MotorMount.png)
  
- [Leg](./Leg.stl)
  - Quantity: 2
  - Setting: Common Settings
  ![Leg](./assets/Leg.png)
  
- [Limit Switch Mount](./LimitSwitchMount.stl)
  - Quantity: 1
  - Setting: Common Settings
  ![Limit Switch Mount](./assets/LimitSwitchMount.png)
  
- Pulley Mounts
  - [PulleyMountA_L.stl](./PulleyMountA_L.stl) (1)
  - [PulleyMountA_R.stl](./PulleyMountA_R.stl) (1)
  - [PulleyMountB.stl](./PulleyMountB.stl) (1)
  - [PulleyMountC.stl](./PulleyMountC.stl) (1)
  - Setting: Common Settings
  ![Pulley Mount](./assets/PulleyMount.png)
  
- [Arm Holder](./Arm_Holder.stl)
  - Quantity: 1
  - Setting: Common Settings
  - Generates a large amount of supports.
  - Support filament is strongly recommended.
  ![Arm Holder](./assets/ArmHolder.png)
  
- [Stopper](./Stopper.stl)
  - Quantity: 2
  - Setting: Common Settings
  ![Stopper](./assets/Stopper.png)

