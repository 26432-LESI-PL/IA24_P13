import re
from constraint import Problem

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

    # Skip line é para passar a linha do Projects summary à frente pois tem um header
    # e o programa não consegue identificar o header como uma linha de dados
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
                data["general_info"]["projects"] = int(re.search(r'projects\s*:\s*(\d+)', line).group(1))
            elif "jobs" in line:
                data["general_info"]["jobs"] = int(re.search(r'jobs \(incl\. supersource/sink \):\s+(\d+)', line).group(1))
            elif "horizon" in line:
                data["general_info"]["horizon"] = int(re.search(r'horizon\s*:\s*(\d+)', line).group(1))
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

file_path = 'P01_DATASET_30.TXT'
dataset = read_dataset(file_path)

# Inicializar o problema
problem = Problem()
# Obter a data de vencimento (due_date) do primeiro projeto
due_date = dataset["projects_summary"][0]["due_date"]

# Criar variáveis para cada tarefa (domínio = intervalo de início até o due_date)
for job in dataset["durations_resources"]:
    jobnr = job["jobnr"]
    problem.addVariable(jobnr, range(due_date + 1))  # Domínio vai até due_date, inclusive

# Restrições de precedência
for relation in dataset["precedence_relations"]:
    job = relation["jobnr"]
    successors = relation["successors"]
    duration = next(j["duration"] for j in dataset["durations_resources"] if j["jobnr"] == job)

    for successor in successors:
        problem.addConstraint(lambda j_start, s_start, d=duration: s_start >= j_start + d, [job, successor])

# Restrições de recursos (renováveis)
resource_limits = dataset["resource_availability"]

# Função para verificar o uso de recursos em um instante
def resource_constraint(*args):
    resource_usage = {resource: [0] * (due_date + 1) for resource in resource_limits}
    for idx, start_time in enumerate(args):
        job = dataset["durations_resources"][idx]
        duration = job["duration"]
        resources = job["resources"]

        for t in range(start_time, start_time + duration):
            if t <= due_date:  # Verificar apenas até o due_date
                for r_idx, qty in enumerate(resources):
                    resource = f'R{r_idx + 1}'
                    resource_usage[resource][t] += qty
                    if resource_usage[resource][t] > resource_limits[resource]:
                        return False
    return True

# Adicionar restrição de recursos
problem.addConstraint(resource_constraint, [job["jobnr"] for job in dataset["durations_resources"]])

# Restrições de duração (limitar ao due_date)
for job in dataset["durations_resources"]:
    jobnr = job["jobnr"]
    duration = job["duration"]
    problem.addConstraint(lambda start, d=duration: start + d <= due_date, [jobnr])

# Resolver o problema
solution = problem.getSolution()

# Calcular o makespan
tasks = dataset["durations_resources"]
makespan = max(solution[task["jobnr"]] + task["duration"] for task in tasks)
print(f"\nMakespan: {makespan}")

# Exibir a solução organizada
if solution:
    sorted_tasks = sorted(solution.items(), key=lambda x: x[1])  # Ordena pelo tempo de início

    print("Solução organizada (por tempo de início):")
    for task, start_time in sorted_tasks:
        duration = next(d["duration"] for d in dataset["durations_resources"] if d["jobnr"] == task)
        end_time = start_time + duration
        print(f"Tarefa {task}: começa em {start_time}, termina em {end_time}")
else:
    print("Nenhuma solução viável encontrada.")
