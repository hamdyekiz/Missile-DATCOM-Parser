import subprocess
import re
import csv
import math
import os

# File paths
filename = "for005.dat"
output_filename = "for006.dat"

# Parameter setup
mach_step_size = 0.5
mach_min = 0.01
mach_max = 5
mach_total_step_size = math.ceil((mach_max - mach_min) / mach_step_size) + 1
mach_values = [mach_step_size * i + mach_min for i in range(mach_total_step_size)]

alpha_step_size = 2
alpha_min = -16
alpha_max = 16
alpha_total_step_size = math.ceil((alpha_max - alpha_min) / alpha_step_size) + 2
alpha_values = [alpha_step_size * (i - 1) + alpha_min for i in range(1, alpha_total_step_size)]

# Read original for005.dat template
with open(filename, "r") as f:
    original_lines = f.readlines()

# Prepare header
csv_rows = []
header = ["ALPHA", "MACH", "Q", "CN", "CM", "CA", "CY", "CLN", "CLL",
          "CL", "CD", "CLCD", "XCP", "CNA", "CMA", "CYB", "CLNB", "CLLB",
          "CNQ", "CMQ", "CAQ", "CNAD", "CMAD",
          "CYR", "CLNR", "CLLR", "CYP", "CLNP", "CLLP"]
csv_rows.append(header)

def parse_for006(filepath="for006.dat"):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    dynamic_pressure = float("nan")
    longitudinal_data = []
    lateral_data = []
    derivatives_data = []
    dynamic_derivatives_data = []
    dynamic_yaw_roll_data = []

    flags = {
        "long_block": False,
        "lat_block": False,
        "deriv_block": False,
        "dyn_block": False,
        "dyn_yaw_block": False
    }

    found = {
        "long": False,
        "lat": False,
        "deriv": False,
        "dyn": False,
        "dyn_yaw": False
    }

    for line in lines:
        line = line.strip()

        # === Dynamic Pressure ===
        if "DYNAMIC PRESSURE" in line and "LB/FT**2" in line and not math.isfinite(dynamic_pressure):
            match = re.search(r"DYNAMIC PRESSURE\s*=\s*([0-9Ee.+-]+)", line)
            if match:
                dynamic_pressure = float(match.group(1))

        # === Section triggers ===
        if "LONGITUDINAL" in line and not found["long"]:
            flags["long_block"] = True
            continue
        if all(x in line for x in ["ALPHA", "CL", "CD", "CL/CD", "X-C.P."]) and not found["lat"]:
            flags["lat_block"] = True
            continue
        if "DERIVATIVES (PER RADIAN)" in line and not found["deriv"]:
            flags["deriv_block"] = True
            continue
        if "DYNAMIC DERIVATIVES (PER RADIAN)" in line:
            if not found["dyn"]:
                flags["dyn_block"] = True
                continue
            elif not found["dyn_yaw"]:
                flags["dyn_yaw_block"] = True
                continue

        parts = line.split()
        if not parts or "ALPHA" in line:
            continue

        try:
            nums = list(map(float, parts))
        except ValueError:
            continue

        if flags["long_block"] and not found["long"] and len(nums) >= 7:
            longitudinal_data = nums[1:7]
            found["long"] = True
            flags["long_block"] = False
        elif flags["lat_block"] and not found["lat"] and len(nums) >= 5:
            lateral_data = nums[1:5]
            found["lat"] = True
            flags["lat_block"] = False
        elif flags["deriv_block"] and not found["deriv"] and len(nums) >= 6:
            derivatives_data = nums[1:6]
            found["deriv"] = True
            flags["deriv_block"] = False
        elif flags["dyn_block"] and not found["dyn"] and len(nums) >= 6:
            dynamic_derivatives_data = nums[1:6]
            found["dyn"] = True
            flags["dyn_block"] = False
        elif flags["dyn_yaw_block"] and not found["dyn_yaw"] and len(nums) >= 7:
            dynamic_yaw_roll_data = nums[1:7]
            found["dyn_yaw"] = True
            flags["dyn_yaw_block"] = False

    # Combine all
    aero_derivatives = longitudinal_data + lateral_data + derivatives_data + dynamic_derivatives_data + dynamic_yaw_roll_data
    return dynamic_pressure, aero_derivatives

# === Main Loop ===
for alpha in alpha_values:
    for mach in mach_values:
        new_lines = []
        for line in original_lines:
            if line.strip().startswith("MACH"):
                prefix, _ = line.split("=", 1)
                new_line = f"{prefix}= {format(mach, '.2f')},\n"
                new_lines.append(new_line)
            elif line.strip().startswith("ALPHA"):
                prefix, _ = line.split("=", 1)
                new_line = f"{prefix}= {format(alpha, '.2f')},\n"
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        # Write for005.dat
        with open(filename, "w") as f:
            f.writelines(new_lines)

        # Run DATCOM
        print(f"Running datcom97.exe with ALPHA = {alpha}, MACH = {mach}")
        subprocess.run(["datcom97.exe"], check=True)

        # Extract data
        dyn_q, aero_coeffs = parse_for006(output_filename)
        row = [format(alpha, ".3f"), format(mach, ".3f"), format(dyn_q, ".3f")]
        row += [format(val, ".3f") for val in aero_coeffs]
        csv_rows.append(row)

# Write to per-alpha CSVs
output_folder = "coef_output"
os.makedirs(output_folder, exist_ok=True)

for alpha in alpha_values:
    alpha_str = format(alpha, ".3f")
    file_path = os.path.join(output_folder, f"alpha{format(alpha, '.2f')}.csv")

    # Force delete if already exists
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except PermissionError:
        print(f"❌ ERROR: File {file_path} is in use. Please close it and re-run.")
        continue

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        rows_copy = [row for row in csv_rows[1:] if row[0] == alpha_str]
        writer.writerows(rows_copy)


print("CSV files written to 'coef_output' folder.")
