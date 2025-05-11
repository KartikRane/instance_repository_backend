from config import Cvrp2DInstance, Cvrp2DCustomer
import lzma
from pathlib import Path
from uuid import uuid4


def write_to_json_xz(data: Cvrp2DInstance):
    """Write a Cvrp2DInstance to a compressed JSON (.json.xz) file."""
    path = Path(f"./instances/{data.instance_uid}.json.xz")
    path.parent.mkdir(parents=True, exist_ok=True)
    with lzma.open(path, "wt") as f:
        f.write(data.json(indent=2))


def parse_vrp_2d(file_path: Path) -> Cvrp2DInstance:
    """
    Parse a .vrp file and return a Cvrp2DInstance containing only customer coordinates and demands.
    Assumes depot is node 1 and should be ignored in output.
    """
    lines = file_path.read_text().splitlines()

    node_section = False
    demand_section = False
    depot_section = False

    coords = {}
    demands = {}

    for line in lines:
        line = line.strip()

        # Switch sections
        if line == "NODE_COORD_SECTION":
            node_section = True
            demand_section = depot_section = False
            continue
        elif line == "DEMAND_SECTION":
            demand_section = True
            node_section = depot_section = False
            continue
        elif line == "DEPOT_SECTION":
            depot_section = True
            node_section = demand_section = False
            continue
        elif line == "EOF":
            break

        # Read coordinates
        if node_section:
            parts = line.split()
            if len(parts) == 3:
                node_id = int(parts[0])
                x, y = float(parts[1]), float(parts[2])
                coords[node_id] = (x, y)

        # Read demands
        if demand_section:
            parts = line.split()
            if len(parts) == 2:
                node_id = int(parts[0])
                demand = int(parts[1])
                demands[node_id] = demand

    # Build customer list, excluding depot (ID 1)
    customers = []
    for node_id in sorted(coords.keys()):
        if node_id == 1:  # depot
            continue
        customers.append(
            Cvrp2DCustomer(
                customer_id=node_id,
                x=coords[node_id][0],
                y=coords[node_id][1],
                demand=demands[node_id],
            )
        )

    # Create instance
    instance = Cvrp2DInstance(
        instance_uid=f"cvrp2d_{file_path.stem}_{uuid4().hex[:8]}",
        origin="Augerat CVRP Benchmark",
        customers=customers,
    )

    return instance


if __name__ == "__main__":
    folder = Path("./benchmark_instances/Set_A")
    vrp_files = list(folder.glob("*.vrp"))

    if not vrp_files:
        print("⚠️ No .vrp files found in ./benchmark_instances/Set_A")
    else:
        for file_path in vrp_files:
            try:
                print(f"🔄 Processing: {file_path.name}")
                instance = parse_vrp_2d(file_path)
                write_to_json_xz(instance)
            except Exception as e:
                print(f"Error in {file_path.name}: {e}")

        print("All CVRP_2D instances processed.")
