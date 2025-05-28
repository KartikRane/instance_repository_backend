from config import CvrpInstance
import lzma
import math
import urllib.request
from pathlib import Path
from zipfile import ZipFile
from uuid import uuid4

CVRP_ZIP_URL = "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-A.zip"
CVRP_ZIP_PATH = Path("data/cvrp_benchmarks.zip")
CVRP_EXTRACT_DIR = Path("data/cvrp_benchmarks")
INSTANCE_OUTPUT_DIR = Path("./instances")

def download_and_extract_cvrp_zip():
    if not CVRP_ZIP_PATH.exists():
        print(f" Downloading CVRP benchmark zip from {CVRP_ZIP_URL}")
        CVRP_ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(CVRP_ZIP_URL, CVRP_ZIP_PATH)

    if not CVRP_EXTRACT_DIR.exists():
        print(f" Extracting {CVRP_ZIP_PATH} to {CVRP_EXTRACT_DIR}")
        with ZipFile(CVRP_ZIP_PATH, "r") as zip_ref:
            zip_ref.extractall(CVRP_EXTRACT_DIR)

def write_to_json_xz(data: CvrpInstance):
    """Write a CvrpInstance to a compressed .json.xz file."""
    instance_uid = data.instance_uid
    path = INSTANCE_OUTPUT_DIR / f"{instance_uid}.json.xz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with lzma.open(path, "wt") as f:
        f.write(data.json())


def compute_euclidean_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def parse_cvrp(file_path: Path, instance_number: int):
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

    # Organize data
    depot_coord = coords[depot_id]
    customers = []
    customer_demands = []

    for node_id in sorted(coords.keys()):
        if node_id != depot_id:
            customers.append(coords[node_id])
            customer_demands.append(demands[node_id])

    # Compute distance matrix (depot + customers)
    locations = [depot_coord] + customers
    distance_matrix = [
        [compute_euclidean_distance(loc1, loc2) for loc2 in locations]
        for loc1 in locations
    ]

    instance = CvrpInstance(
        instance_uid=f"CVRPLIB/{file_path.stem}/{instance_number}",
        origin="http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/A/A-n32-k5.vrp",
        vehicle_capacity=vehicle_capacity,
        depot=depot_coord,
        customers=customers,
        demands=customer_demands,
        distance_matrix=distance_matrix,
    )

    print(f"✓ Processed: {file_path.name}")
    print(f"  → num_customers: {len(customers)}")
    print(f"  → total_demand: {sum(customer_demands)}")
    print(f"  → distance_matrix size: {len(distance_matrix)}x{len(distance_matrix[0])}")

    # Save instance
    write_to_json_xz(instance)


if __name__ == "__main__":
    download_and_extract_cvrp_zip()

    vrp_files = sorted(CVRP_EXTRACT_DIR.rglob("*.vrp"))
    for instance_number, file_path in enumerate(vrp_files, 1):
        try:
            print(f" Processing: {file_path.name}")
            parse_cvrp(file_path, instance_number)
        except Exception as e:
            print(f" ERROR processing {file_path.name}: {e}")

    print(" All CVRP instances processed.")
