from config import CvrpInstance
import lzma
from pathlib import Path
from uuid import uuid4


def write_to_json_xz(data: CvrpInstance):
    """Write a CvrpInstance to a compressed .json.xz file."""
    instance_uid = data.instance_uid
    path = Path(f"./instances/{instance_uid}.json.xz")
    path.parent.mkdir(parents=True, exist_ok=True)
    with lzma.open(path, "wt") as f:
        f.write(data.json())


def parse_cvrp(file_path: str):
    """Parse a CVRP .vrp file and save as CvrpInstance."""
    with open(file_path, "r") as file:
        lines = file.readlines()

    vehicle_capacity = None
    node_coord_section = False
    demand_section = False
    depot_section = False

    coords = {}
    demands = {}
    depot_id = None

    for line in lines:
        line = line.strip()

        if line.startswith("CAPACITY"):
            vehicle_capacity = int(line.split(":")[1].strip())

        elif line == "NODE_COORD_SECTION":
            node_coord_section = True
            demand_section = False
            depot_section = False
            continue

        elif line == "DEMAND_SECTION":
            node_coord_section = False
            demand_section = True
            depot_section = False
            continue

        elif line == "DEPOT_SECTION":
            node_coord_section = False
            demand_section = False
            depot_section = True
            continue

        elif line == "EOF":
            break

        # Reading coordinates
        if node_coord_section:
            parts = line.split()
            node_id = int(parts[0])
            x, y = float(parts[1]), float(parts[2])
            coords[node_id] = (x, y)

        # Reading demands
        if demand_section:
            parts = line.split()
            node_id = int(parts[0])
            demand = int(parts[1])
            demands[node_id] = demand

        # Reading depot
        if depot_section:
            if line != "-1":
                depot_id = int(line)

    if depot_id is None:
        raise ValueError("Depot ID not found in the file.")

    # Now organize data
    depot_coord = coords[depot_id]
    customers = []
    customer_demands = []

    for node_id in sorted(coords.keys()):
        if node_id != depot_id:
            customers.append(coords[node_id])
            customer_demands.append(demands[node_id])

    # Create instance
    instance = CvrpInstance(
        instance_uid=str(uuid4()),
        origin="cvrp_benchmark",
        vehicle_capacity=vehicle_capacity,
        depot=depot_coord,
        customers=customers,
        demands=customer_demands,
    )

    print(f"✓ Processed: {file_path.name}")
    print(f"  → num_customers: {instance.num_customers}")
    print(f"  → relative_vehicle_capacity: {instance.relative_vehicle_capacity:.4f}")
    print(
        f"  → max_mean_customers_per_tour: {instance.max_mean_customers_per_tour:.2f}"
    )

    # Save instance
    write_to_json_xz(instance)


if __name__ == "__main__":
    folder = Path("./benchmark_src/Set_A")
    for file_path in folder.glob("*.vrp"):
        try:
            print(f"Processing: {file_path.name}")
            parse_cvrp(str(file_path))
        except Exception as e:
            print(f" ERROR processing {file_path.name}: {e}")

    print("All CVRP instances processed.")
