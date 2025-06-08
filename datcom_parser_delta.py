import subprocess
import re
import csv
import math
import os
import shutil

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

xcg_step_size = 0.1
xcg_min = 2.1
xcg_max = 2.4
xcg_total_step_size = (math.ceil((xcg_max - xcg_min) / xcg_step_size) + 2)
xcg_values = [xcg_step_size * (i - 1) + xcg_min for i in range(1, xcg_total_step_size)]

delta_min  = -15.0    
delta_max  = 15.0  
delta_step = 1 

delta_values = []
d = delta_min
while d <= delta_max + 1e-8:
    delta_values.append(round(d, 6))
    d += delta_step

with open(filename, "r") as f:
    original_lines = f.readlines()


csv_rows = []
header = [
    "XCG","ALPHA","MACH","DELTA","Q","CN","CM","CA","CY","CLN","CLL",
    "CL","CD","CLCD","XCP","CNA","CMA","CYB","CLNB","CLLB",
    "CNQ","CMQ","CAQ","CNAD","CMAD",
    "CYR","CLNR","CLLR","CYP","CLNP","CLLP"
]
csv_rows.append(header)

# compile regex for DELTA2
delta2_pattern = re.compile(r'^(?P<prefix>\s*DELTA2\s*=\s*)([-0-9.,]+)(?P<suffix>\$)')

def parse_for006(filepath="for006.dat"):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    dynamic_pressure = float('nan')
    longitudinal_data = []
    lateral_data = []
    derivatives_data = []
    dynamic_derivatives_data = []
    dynamic_yaw_roll_data = []

    flags = {k: False for k in ["long_block","lat_block","deriv_block","dyn_block","dyn_yaw_block"]}
    found = {k: False for k in ["long","lat","deriv","dyn","dyn_yaw"]}

    for line in lines:
        l = line.strip()
        if "DYNAMIC PRESSURE" in l and "LB/FT**2" in l and not math.isfinite(dynamic_pressure):
            m = re.search(r"DYNAMIC PRESSURE\s*=\s*([0-9Ee.+-]+)", l)
            if m: dynamic_pressure = float(m.group(1))

        if "LONGITUDINAL" in l and not found["long"]:
            flags["long_block"] = True; continue
        if all(x in l for x in ["ALPHA","CL","CD","CL/CD","X-C.P."]) and not found['lat']:
            flags['lat_block'] = True; continue
        if "DERIVATIVES (PER RADIAN)" in l and not found['deriv']:
            flags['deriv_block'] = True; continue
        if "DYNAMIC DERIVATIVES (PER RADIAN)" in l:
            if not found['dyn']:
                flags['dyn_block'] = True; continue
            elif not found['dyn_yaw']:
                flags['dyn_yaw_block'] = True; continue

        parts = l.split()
        if not parts or "ALPHA" in l: continue
        try:
            nums = list(map(float, parts))
        except ValueError:
            continue

        if flags['long_block'] and not found['long'] and len(nums)>=7:
            longitudinal_data = nums[1:7]; found['long']=True; flags['long_block']=False
        elif flags['lat_block'] and not found['lat'] and len(nums)>=5:
            lateral_data = nums[1:5]; found['lat']=True; flags['lat_block']=False
        elif flags['deriv_block'] and not found['deriv'] and len(nums)>=6:
            derivatives_data = nums[1:6]; found['deriv']=True; flags['deriv_block']=False
        elif flags['dyn_block'] and not found['dyn'] and len(nums)>=6:
            dynamic_derivatives_data = nums[1:6]; found['dyn']=True; flags['dyn_block']=False
        elif flags['dyn_yaw_block'] and not found['dyn_yaw'] and len(nums)>=7:
            dynamic_yaw_roll_data = nums[1:7]; found['dyn_yaw']=True; flags['dyn_yaw_block']=False

    return dynamic_pressure, (
        longitudinal_data + lateral_data + derivatives_data +
        dynamic_derivatives_data + dynamic_yaw_roll_data
    )

# === Main Loop ===
for alpha in alpha_values:
    for mach in mach_values:
        for xcg in xcg_values:
            for delta in delta_values:
                new_lines = []
                for line in original_lines:
                    if line.strip().startswith("MACH"):
                        p,_ = line.split("=",1)
                        new_lines.append(f"{p}= {mach:.2f},\n")
                    elif line.strip().startswith("ALPHA"):
                        p,_ = line.split("=",1)
                        new_lines.append(f"{p}= {alpha:.2f},\n")
                    elif line.strip().startswith("XCG"):
                        p,_ = line.split("=",1)
                        new_lines.append(f"{p}= {xcg:.2f},\n")
                    else:
                        m = delta2_pattern.match(line)
                        if m:
                            vals = ["0.0", f"{(-delta):.2f}", "0.0", f"{delta:.2f}"]
                            new_lines.append(f"{m.group('prefix')}{','.join(vals)}{m.group('suffix')}\n")
                        else:
                            new_lines.append(line)

                with open(filename,'w') as f: f.writelines(new_lines)
                print(f"Running DATCOM: alpha={alpha}, mach={mach}, xcg={xcg}, delta={delta}")
                subprocess.run(["datcom97.exe"], check=True)

                dyn_q, coeffs = parse_for006(output_filename)
                cn, cm, ca = coeffs[0], coeffs[1], coeffs[2]

                row = [
                    f"{xcg:.3f}", f"{alpha:.3f}", f"{mach:.3f}", f"{delta:.3f}",
                    f"{dyn_q:.3f}", f"{cn:.3f}", f"{cm:.3f}", f"{ca:.3f}"
                ] + [f"{v:.3f}" for v in coeffs[3:]]
                csv_rows.append(row)

# Write results
output_folder = "coef_output"
os.makedirs(output_folder, exist_ok=True)
for xcg in xcg_values:
    xcg_str = f"{xcg:.3f}"
    path = os.path.join(output_folder, f"xcg{xcg_str}")
    if os.path.isdir(path): shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)
    for alpha in alpha_values:
        alpha_str = f"{alpha:.3f}"
        file_path = os.path.join(path, f"alpha{alpha:.2f}.csv")
        with open(file_path,'w',newline='') as f:
            w = csv.writer(f)
            w.writerow(header)
            rows = [r for r in csv_rows[1:] if r[0]==xcg_str and r[1]==alpha_str]
            w.writerows(rows)
print("CSV files written to 'coef_output' folder.")
