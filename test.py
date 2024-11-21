from constraint import Problem

def read_dataset(file_path):
    dataset = {
        "general_info": {},
        "projects_summary": [],
        "precedence_relations": [],
        "durations_resources": [],
        "resource_availability": {}
    }
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    section = None
    for line in lines:
        line = line.strip()
        if line.startswith("#"):
            if "General Information" in line:
                section = "general_info"
            elif "Projects summary" in line:
                section = "projects_summary"
            elif "Precedence relations" in line:
                section = "precedence_relations"
            elif "Duration and resources" in line:
                section = "durations_resources"
            elif "Resource availability" in line:
                section = "resource_availability"
            continue
        
        if section == "general_info":
            if "projects" in line:
                dataset["general_info"]["projects"] = int(line.split(":")[1].strip())
            elif "jobs (incl. supersource/sink )" in line:
                dataset["general_info"]["jobs"] = int(line.split(":")[1].strip())
            elif "horizon" in line:
                dataset["general_info"]["horizon"] = int(line.split(":")[1].strip())
        
 
        elif section == "projects_summary":
            if line and not line.startswith("#") and not line.startswith("pronr") and not line.startswith("*"):
                parts = line.split()
                dataset["projects_summary"].append({
                    "pronr": int(parts[0]),
                    "jobs": int(parts[1]),
                    "rel_date": int(parts[2]),
                    "due_date": int(parts[3]),
                    "tard_cost": int(parts[4]),
                    "mpm_time": int(parts[5])
                })
        
        elif section == "precedence_relations":
            if line and not line.startswith("#") and not line.startswith("*"):
                parts = line.split()
                jobnr = int(parts[0])
                modes = int(parts[1])
                successors = list(map(int, parts[3:]))
                dataset["precedence_relations"].append({
                    "jobnr": jobnr,
                    "modes": modes,
                    "successors": successors
                })
        
        elif section == "durations_resources":
            if line and not line.startswith("#") and not line.startswith("*"):
                parts = line.split()
                jobnr = int(parts[0])
                mode = int(parts[1])
                duration = int(parts[2])
                resources = list(map(int, parts[3:]))
                dataset["durations_resources"].append({
                    "jobnr": jobnr,
                    "mode": mode,
                    "duration": duration,
                    "resources": resources
                })
        
        elif section == "resource_availability":
            if line and not line.startswith("#") and not line.startswith("*"):
                parts = line.split()
                resource = parts[0]
                qty = int(parts[1])
                dataset["resource_availability"][resource] = qty

    return dataset

file_path = 'P01_DATASET_10.TXT'
dataset = read_dataset(file_path)

# Inicializar o problema
problem = Problem()

# Obter informações gerais
due_date = dataset["projects_summary"][0]["due_date"]

# Criar variáveis para cada tarefa e modo de execução (domínio = intervalo de início até a due date)
for job in dataset["durations_resources"]:
    jobnr = job["jobnr"]
    mode = job["mode"]
    problem.addVariable((jobnr, mode), range(due_date + 1))  # Domínio baseado na due date

# Restrições de precedência
for relation in dataset["precedence_relations"]:
    job = relation["jobnr"]
    successors = relation["successors"]
    duration = next(j["duration"] for j in dataset["durations_resources"] if j["jobnr"] == job)

    for successor in successors:
        problem.addConstraint(lambda j_start, s_start, d=duration: s_start >= j_start + d, [(job, 1), (successor, 1)])

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
            if t > due_date:
                return False  # Garantir que a tarefa não ultrapasse a due date
            for r_idx, qty in enumerate(resources):
                resource = f'R{r_idx + 1}'
                resource_usage[resource][t] += qty
                if resource_usage[resource][t] > resource_limits[resource]:
                    return False
    return True

# Adicionar restrição de recursos
problem.addConstraint(resource_constraint, [(job["jobnr"], job["mode"]) for job in dataset["durations_resources"]])

# Restrições de horizonte de tempo (usando due date)
for job in dataset["durations_resources"]:
    jobnr = job["jobnr"]
    duration = job["duration"]
    problem.addConstraint(lambda start, d=duration: start + d <= due_date, [(jobnr, job["mode"])])

# Resolver o problema
print("Solving the problem...")
solution = problem.getSolution()
print("Solution found.")

# Calcular o makespan
if solution:
    tasks = dataset["durations_resources"]
    makespan = max(solution[(task["jobnr"], task["mode"])] + task["duration"] for task in tasks)
    print(f"\nMakespan: {makespan}")

    # Exibir a solução
    # Organiza as tarefas pelo tempo de início (os valores de 'solution' são os tempos de início)
    sorted_tasks = sorted(solution.items(), key=lambda x: x[1])  # Ordena pelo tempo de início
    print("Solução organizada (por tempo de início):")
    for (task, mode), start_time in sorted_tasks:
        # Calcula o tempo de término com base na duração da tarefa
        duration = next(d["duration"] for d in dataset["durations_resources"] if d["jobnr"] == task and d["mode"] == mode)
        end_time = start_time + duration
        print(f"Tarefa {task}: começa em {start_time}, termina em {end_time}")
else:
    print("Nenhuma solução viável encontrada.")