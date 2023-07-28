import sys
import subprocess
import time

def gen_capacity_constraints_st(src, trans, dest):
    capacity_constraints_st = ""
    for i in range(1, src + 1):
        for k in range(1, trans + 1):
            temp = [f"x{i}{k}{j}" for j in range(1, dest + 1)]
            string = " + ".join(temp) + f" - c{i}{k} <= 0"
            capacity_constraints_st += f"{string}\n"
    return capacity_constraints_st

def gen_capacity_constraints_td(src, trans, dest):
    capacity_constraints_td = ""
    for k in range(1, trans + 1):
        for j in range(1, dest + 1):
            temp = [f"x{i}{k}{j}" for i in range(1, src + 1)]
            string = " + ".join(temp) + f" - d{k}{j} <= 0"
            capacity_constraints_td += f"{string}\n"
    return capacity_constraints_td

def gen_demand_constraints(src, trans, dest):
    demand_constraints = ""
    for i in range(1, src + 1):
        for j in range(1, dest + 1):
            temp = [f'x{i}{k}{j}' for k in range(1, trans + 1)]
            string = " + ".join(temp) + f" = {i + j}"
            demand_constraints += f"{string}\n"
    return demand_constraints

def gen_binary_constraints(src, trans, dest, paths):
    binary_constraints = ""
    for i in range(1, src + 1):
        for j in range(1, dest + 1):
            temp = [f"u{i}{k}{j}" for k in range(1, trans + 1)]
            string = " + ".join(temp) + f" = {paths}"
            binary_constraints += f"{string}\n"
    return binary_constraints

def gen_transit_load_constraints(src, trans, dest):
    transit_load_constraints = ""
    for k in range(1, trans + 1):
        constraint = ""
        for j in range(1, src + 1):
            for i in range(1, dest + 1):
                if constraint != "":
                    constraint += " + "
                constraint += f"x{i}{k}{j}"
        constraint += f" - r <= 0"
        transit_load_constraints += f"{constraint}\n"
    return transit_load_constraints

def gen_flow_constraints(src, trans, dest, paths):
    flow_constraints = ""
    for i in range(1, src + 1):
        for j in range(1, dest + 1):
            temp = [f"{paths} x{i}{k}{j} - {i + j} u{i}{k}{j} = 0" for k in range(1, trans + 1)]
            flow_constraints += "\n".join(temp) + "\n"
    return flow_constraints

def gen_bound_constraints(src, trans, dest):
    bound_constraints = ""
    for i in range(1, src + 1):
        for j in range(1, dest + 1):
            for k in range(1, trans + 1):
                bound_constraints += f"0 <= x{i}{k}{j}\n"
    return bound_constraints

def gen_binary_variables(src, trans, dest):
    binary_variables = ""
    for i in range(1, src + 1):
        for j in range(1, trans + 1):
            for k in range(1, dest + 1):
                binary_variables += f"u{i}{k}{j}\n"
    return binary_variables

def assemble_lp_file(demand_constraint, capacity_constraints_st, capacity_constraints_td, bound_constraints,
                     binary_variables, binary_constraints, flow_constraints, transit_load_constraints):
    with open('Documents/temp.lp', 'w') as f:
        f.write("Minimize\n r\nSubject to\n")
        f.write("Capacity source to transit: \n")
        f.write(capacity_constraints_st)

        f.write("Capacity transit to destination: \n")
        f.write(capacity_constraints_td)

        f.write("demand constraint:\n")
        f.write(demand_constraint)

        f.write("Transit load constraints: \n")
        f.write(transit_load_constraints)

        f.write("Demand flow: \n")
        f.write(flow_constraints)

        f.write("Binary variable constraints: \n")
        f.write(binary_constraints)

        f.write("Bounds \n")
        f.write(bound_constraints)
        f.write("0 <= r\n")

        f.write("Binary \n")
        f.write(binary_variables)

        f.write("End")

def run_cplex():
    transit_load = {}
    load = 0
    max_node = 0
    capture_load = {}

    link_count = 0
    highest_capacity = {}
    max_value = 0
    highest_cap = {}

    start_time = time.time()
    args = ["cplex", "-c", "read", "Documents/temp.lp", "optimize", "display solution variables -"]
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    output, _ = process.communicate()
    end_time = time.time()
    run_time = end_time - start_time
    result = output.decode().strip()

    lines = result.split('\n')
    for line in lines:
        if line.startswith("x"):
            variable, value = line.split()
            transit_load[variable] = float(value)
        elif line.startswith("c") or line.startswith("d"):
            link_count += 1
            variable, value = line.split()
            highest_capacity[variable] = float(value)
            
    current_Y = 1
    load = 0 
    for n in transit_load:
        if int(n[2]) > max_node:
            max_node = int(n[2])

    while current_Y <= max_node:
        load = 0
        for key in transit_load:
            if key[2] == str(current_Y):
                load += transit_load[key]
        capture_load[current_Y] = load
        current_Y += 1
    
    for key, value in highest_capacity.items():
        if value > max_value:
            max_value = value
            highest_cap.clear()
            highest_cap[key] = value
        elif value == max_value:
            highest_cap[key] = value

    print(f"Num links {link_count}")
    for key, value in highest_cap.items():
        print(f"link {key} : value {value}")

    for key, value in capture_load.items():
        print(f" node {key} : load {value}")
    return run_time, capture_load, highest_cap

def write_lp(Y):
    # if len(sys.argv) < 4:
    #     print("input three arguments: source nodes, transit nodes, destination nodes.")
    #     exit(-1)

    X = 3 #int(sys.argv[1])
    # Y =   int(sys.argv[2])
    Z = 3 #int(sys.argv[3])

    paths = 2
    demand_constraint = gen_demand_constraints(X, Y, Z)
    capacity_constraints_st = gen_capacity_constraints_st(X, Y, Z)
    capacity_constraints_td = gen_capacity_constraints_td(X, Y, Z)
    bound_constraints = gen_bound_constraints(X, Y, Z)
    binary_variables = gen_binary_variables(X, Y, Z)
    binary_constraints = gen_binary_constraints(X, Y, Z, paths)
    flow_constraints = gen_flow_constraints(X, Y, Z, paths)
    transit_load_constraints = gen_transit_load_constraints(X, Y, Z)
    assemble_lp_file(demand_constraint, capacity_constraints_st, capacity_constraints_td, bound_constraints,
                     binary_variables, binary_constraints, flow_constraints, transit_load_constraints)

def main():
    for Y in range(2, 3):
        write_lp(Y)
        run_time, transit_load, highest_capacity = run_cplex()
        print(f"Y = {Y}")
        print("CPLEX run time:", run_time)
        print("Transit load:", transit_load)
        print("Highest link capacity:", highest_capacity)
        print()

if __name__ == "__main__":
    main()