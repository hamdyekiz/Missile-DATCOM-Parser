# 🚀 Missile DATCOM Parser
[![Python 3.6+](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

This Python script automates the process of running [Missile DATCOM](https://en.wikipedia.org/wiki/Missile_Datcom) simulations across a defined grid of flight conditions. It updates the `for005.dat` input file for each case, runs `datcom97.exe`, extracts aerodynamic coefficients from the output file (`for006.dat`), and saves the results into organized CSV files for further analysis.

---

## Key Features

- **Simulation** over:
  - **Mach number**: customizable range and step
  - **Angle of attack (ALPHA)**: customizable range and step
  - **Center of gravity (XCG)**: customizable range and step
  - **Deflewction angle (DELTA)**: customizable range and step

- Automatically modifies `for005.dat` for each test case
- Executes `datcom97.exe` via subprocess
- Parses aerodynamic and stability coefficients from `for006.dat`
- Exports results into neatly structured CSV files per `XCG`, `ALPHA` and `DELTA`

---

## File Structure
```plaintext
project-root/
├── datcom_parser_xcg.py       # Main script
├── datcom97.exe               # Executable for Missile DATCOM
├── for004.dat                
├── for005.dat                 # DATCOM User input file
├── for006.dat                 # DATCOM output file
├── coef_output/               # Output folder (created by script)
│   ├── xcg2.10/
│   │   ├── alpha-16.00.csv
│   │   ├── alpha-15.00.csv
│   │   └── ...
│   ├── xcg2.25/
│   │   ├── alpha-16.00.csv
│   │   └── ...
│   └── ...
└── ...
```
Example output CSV file: [example.csv](https://github.com/hamdyekiz/Missile-DATCOM-Parser/blob/main/alpha0.00.csv)

---

## Output Overview

Results are saved in the `coef_output/` directory. For each XCG value, a subfolder is created containing CSV files—one for each angle of attack. Each CSV contains the full range of Mach values for that configuration.

Each row includes input parameters (`XCG`, `ALPHA`, `MACH`, and dynamic pressure `Q`), followed by:

- **Static coefficients**: CN, CM, CA, CY, CL, CD, CL/CD, XCP
- **Stability derivatives**: CNA, CMA, CYB, CLNB, CLLB
- **Dynamic derivatives**: CNQ, CMQ, CAQ, CMAD, CYR, CLNR, CLLR, CYP, CLNP, CLLP

---
  
## Requirements

- Python 3.6 or newer
- `datcom97.exe` in the same directory or available via system PATH
- Run the script with:
   ```bash
   python datcom_parser_xcg.py
---

## Parameter Configuration

Before running the script, set the flight condition ranges in the Python file

```python
# Mach number settings
mach_step_size = 0.25
mach_min = 0.01
mach_max = 5.0
mach_total_step_size = math.ceil((mach_max - mach_min) / mach_step_size) + 1
mach_values = [mach_step_size * i + mach_min for i in range(mach_total_step_size)]

# Angle of attack (ALPHA) settings
alpha_step_size = 1
alpha_min = -16
alpha_max = 16
alpha_total_step_size = math.ceil((alpha_max - alpha_min) / alpha_step_size) + 2
alpha_values = [alpha_step_size * (i - 1) + alpha_min for i in range(1, alpha_total_step_size)]

# Center of gravity (XCG) settings
xcg_step_size = 0.15
xcg_min = 2.10
xcg_max = 2.40
xcg_total_step_size = math.ceil((xcg_max - xcg_min) / xcg_step_size) + 2
xcg_values = [xcg_step_size * (i - 1) + xcg_min for i in range(1, xcg_total_step_size)]

# Deflection Angle (delta) settings
delta_min  = -25.0    
delta_max  = 20.0  
delta_step = 1
