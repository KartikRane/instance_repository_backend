import logging
import os
import lzma
import math
import urllib.request
from pathlib import Path
from zipfile import ZipFile
from config import PROBLEM_UID, CvrpInstance
from connector import Connector

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# List of CVRP benchmark ZIP URLs
CVRP_ZIP_URLS = [
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-A.zip",
]

def download_and_extract_cvrp_zip(zip_url: str, extract_root: Path):
    zip_name = zip_url.split("/")[-1]
    set_name = zip_name.replace(".zip", "")
    zip_path = extract_root / f"{set_name}.zip"
    extract_dir = extract_root / set_name

    if not zip_path.exists():
        logger.info(f"Downloading {zip_name} from {zip_url}")
        extract_root.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(zip_url, zip_path)

    if not extract_dir.exists():
        logger.info(f"Extracting {zip_path} to {extract_dir}")
        with ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

    return extract_dir, set_name


def compute_euclidean_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def parse_cvrp(file_path: Path, connector: Connector, set_name: str, zip_url: str):
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

    depot_coord = coords[depot_id]
    customers = []
    customer_demands = []

    for node_id in sorted(coords.keys()):
        if node_id != depot_id:
            customers.append(coords[node_id])
            customer_demands.append(demands[node_id])

    locations = [depot_coord] + customers
    distance_matrix = [
        [compute_euclidean_distance(loc1, loc2) for loc2 in locations]
        for loc1 in locations
    ]

    instance = CvrpInstance(
        instance_uid=f"CVRPLIB(dis_Matrix)/{set_name}/{file_path.stem}",
        origin=f"{zip_url} - CVRP benchmark instance from {set_name}",
        vehicle_capacity=vehicle_capacity,
        depot=depot_coord,
        customers=customers,
        demands=customer_demands,
        distance_matrix=distance_matrix,
    )

    connector.upload_instance(instance)


if __name__ == "__main__":
    connector = Connector(
        base_url=os.environ.get("BASE_URL", "http://127.0.0.1"),
        problem_uid=os.environ.get("PROBLEM_UID", PROBLEM_UID),
        api_key=os.environ.get("API_KEY", "3456345-456-456"),
    )

    extract_root = Path("data/cvrp_benchmarks")

    for zip_url in CVRP_ZIP_URLS:
        try:
            extract_dir, set_name = download_and_extract_cvrp_zip(zip_url, extract_root)
            for file_path in extract_dir.rglob("*.vrp"):
                try:
                    logger.info(f"Processing {file_path.name} from {set_name}")
                    parse_cvrp(file_path, connector=connector, set_name=set_name, zip_url=zip_url)
                except Exception as e:
                    logger.error(f"ERROR processing {file_path.name}: {e}")
        except Exception as e:
            logger.error(f"ERROR with {zip_url}: {e}")

    logger.info("All CVRP benchmark sets processed.")
