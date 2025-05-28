import logging
import json
import os
import sys
from config import PROBLEM_UID, Cvrp2DInstance, Customer, Depot
import lzma
from pathlib import Path
from uuid import uuid4
import urllib.request
from zipfile import ZipFile

# Maintain old-style import hack for repository root
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(REPOSITORY_ROOT))

from connector import Connector

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CVRP_ZIP_URL = "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-A.zip"  # <- Can be changed according to the set
CVRP_ZIP_PATH = Path("data/cvrp2d_benchmarks.zip")
CVRP_EXTRACT_DIR = Path("data/cvrp2d_benchmarks")

def download_and_extract_cvrp_zip():
    if not CVRP_ZIP_PATH.exists():
        print(f"Downloading CVRP benchmark zip from {CVRP_ZIP_URL}")
        CVRP_ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(CVRP_ZIP_URL, CVRP_ZIP_PATH)

    if not CVRP_EXTRACT_DIR.exists():
        print(f"Extracting {CVRP_ZIP_PATH} to {CVRP_EXTRACT_DIR}")
        with ZipFile(CVRP_ZIP_PATH, "r") as zip_ref:
            zip_ref.extractall(CVRP_EXTRACT_DIR)

download_and_extract_cvrp_zip()

def write_to_json_xz(data: Cvrp2DInstance):
    path = Path(f"./instances/{data.instance_uid}.json.xz")
    path.parent.mkdir(parents=True, exist_ok=True)
    with lzma.open(path, "wt") as f:
        f.write(data.model_dump_json(indent=2))


def parse_cvrp_2d(file_path: str):
    file_path = Path(file_path)  # converting string to path object
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

        if node_coord_section:
            parts = line.split()
            node_id = int(parts[0])
            x, y = float(parts[1]), float(parts[2])
            coords[node_id] = (x, y)

        if demand_section:
            parts = line.split()
            node_id = int(parts[0])
            demand = int(parts[1])
            demands[node_id] = demand

        if depot_section:
            if line != "-1":
                depot_id = int(line)

    if depot_id is None:
        raise ValueError("Depot ID not found.")

    depot_coords = coords[depot_id]
    depot = Depot(x=depot_coords[0], y=depot_coords[1])

    customers = []
    customer_id = 0
    for cid in sorted(coords.keys()):
        if cid == depot_id:
            continue  # skip depot
        x, y = coords[cid]
        demand = demands[cid]
        customers.append(Customer(x=x, y=y, customer_id=customer_id, demand=demand))
        customer_id += 1



    instance = Cvrp2DInstance(
        instance_uid=f"{file_path.stem}_{uuid4().hex[:8]}",
        origin="cvrp_benchmark_2d",
        vehicle_capacity=vehicle_capacity,
        depot=depot,
        customers=customers,
    )

    write_to_json_xz(instance)

if __name__ == "__main__":

    # Configuration via environment variables
    base_url = os.environ.get('BASE_URL', 'http://127.0.0.1')
    problem_uid = os.environ.get('PROBLEM_UID', PROBLEM_UID)
    api_key = os.environ.get('API_KEY', "3456345-456-456")

    connector = Connector(
        base_url=base_url,
        problem_uid=problem_uid,
        api_key=api_key,
    )
    
    folder = CVRP_EXTRACT_DIR
    for file_path in folder.rglob("*.vrp"):
        try:
            print(f"Processing: {file_path.name}")
            parse_cvrp_2d(str(file_path))
        except Exception as e:
            print(f" ERROR processing {file_path.name}: {e}")

    print("All CVRP_2D instances processed.")
