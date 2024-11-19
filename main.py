import re
import constraint

def read_dataset(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    data = {
        "general_info": {},
        "projects_summary": [],
        "precedence_relations": [],
        "durations_resources": [],
        "resource_availability": {}
    }

    skip_line = False
    section = None
    for line in lines:
        if skip_line:
            skip_line = False
            continue
        line = line.strip()
        if line.startswith("************"):
            continue
        elif line.startswith("#General Information"):
            section = "general_info"
        elif line.startswith("#Projects summary"):
            section = "projects_summary"
            # skip the next line (header)
            skip_line = True
        elif line.startswith("#Precedence relations"):
            section = "precedence_relations"
        elif line.startswith("#Duration and resources"):
            section = "durations_resources"
        elif line.startswith("#Resource availability"):
            section = "resource_availability"
        elif section == "general_info":
            if "projects" in line:
                data["general_info"]["projects"] = int(re.search(r'projects:\s+(\d+)', line).group(1))
            elif "jobs" in line:
                data["general_info"]["jobs"] = int(re.search(r'jobs \(incl\. supersource/sink \):\s+(\d+)', line).group(1))
            elif "horizon" in line:
                data["general_info"]["horizon"] = int(re.search(r'horizon:\s+(\d+)', line).group(1))
            elif "nonrenewable" in line:
                data["general_info"]["nonrenewable_resources"] = int(re.search(r'nonrenewable\s+:\s+(\d+)', line).group(1))            
            elif "renewable" in line:
                data["general_info"]["renewable_resources"] = int(re.search(r'renewable\s+:\s+(\d+)', line).group(1))
            elif "doubly constrained" in line:
                data["general_info"]["doubly_constrained_resources"] = int(re.search(r'doubly constrained\s+:\s+(\d+)', line).group(1))
        elif section == "projects_summary":
            if line and not line.startswith("#"):
                parts = line.split()
                data["projects_summary"].append({
                    "pronr": int(parts[0]),
                    "jobs": int(parts[1]),
                    "rel_date": int(parts[2]),
                    "due_date": int(parts[3]),
                    "tard_cost": int(parts[4]),
                    "mpm_time": int(parts[5])
                })
        elif section == "precedence_relations":
            if line and not line.startswith("#"):
                parts = line.split()
                jobnr = int(parts[0])
                modes = int(parts[1])
                successors_count = int(parts[2])
                successors = list(map(int, parts[3:]))
                data["precedence_relations"].append({
                    "jobnr": jobnr,
                    "modes": modes,
                    "successors_count": successors_count,
                    "successors": successors
                })
        elif section == "durations_resources":
            if line and not line.startswith("#"):
                parts = line.split()
                jobnr = int(parts[0])
                mode = int(parts[1])
                duration = int(parts[2])
                resources = list(map(int, parts[3:]))
                data["durations_resources"].append({
                    "jobnr": jobnr,
                    "mode": mode,
                    "duration": duration,
                    "resources": resources
                })
        elif section == "resource_availability":
            if line and not line.startswith("#"):
                parts = line.split()
                resource = parts[0]
                qty = int(parts[1])
                data["resource_availability"][resource] = qty

    return data

file_path = 'P01_DATASET_8.TXT'
dataset = read_dataset(file_path)

