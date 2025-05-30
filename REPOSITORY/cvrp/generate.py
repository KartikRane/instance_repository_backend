import logging
import os
import math
import urllib.request
from pathlib import Path
from zipfile import ZipFile

from config import PROBLEM_UID, CvrpInstance, Customer, Depot, Location
from connector import Connector

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CVRP_ZIP_URLS = [
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-A.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-B.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-E.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-F.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-M.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-P.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-CMT.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-tai.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-Golden.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-Li.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-X.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-XXL.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-D.zip",
    "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-XML100.zip",
]

def download_and_extract_cvrp_zip(zip_url: str, extract_root: Path):
    zip_name = zip_url.split("/")[-1]
    set_name = zip_name.replace(".zip", "")
    zip_path = extract_root / zip_name
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

def euclidean(p1: Location, p2: Location) -> float:
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def compute_distance_matrix(locations: list[Location]) -> list[list[float]]:
    return [
        [euclidean(locations[i], locations[j]) for j in range(len(locations))]
        for i in range(len(locations))
    ]

def parse_cvrp(file_path: Path, connector: Connector, set_name: str, zip_url: str):
    with open(file_path, "r") as file:
        lines = file.readlines()

    vehicle_capacity = None
    node_coord_section = demand_section = depot_section = False

    coords = {}
    demands = {}
    depot_ids = []

    for line in lines:
        line = line.strip()
        if line.startswith("CAPACITY"):
            vehicle_capacity = int(line.split(":")[1].strip())
        elif line == "NODE_COORD_SECTION":
            node_coord_section, demand_section, depot_section = True, False, False
            continue
        elif line == "DEMAND_SECTION":
            node_coord_section, demand_section, depot_section = False, True, False
            continue
        elif line == "DEPOT_SECTION":
            node_coord_section, demand_section, depot_section = False, False, True
            continue
        elif line == "EOF":
            break

        parts = line.split()
        if node_coord_section and len(parts) >= 3:
            node_id, x, y = map(float, parts[:3])
            coords[int(node_id)] = {"x": x, "y": y}
        elif demand_section and len(parts) >= 2:
            node_id, demand = map(int, parts[:2])
            demands[node_id] = demand
        elif depot_section and line != "-1":
            depot_ids.append(int(line))

    if not depot_ids:
        raise ValueError("No depot found in the file.")

    depot_node_id = depot_ids[0]
    location_id_lookup = {}
    locations: list[Location] = []

    for node_id in sorted(coords.keys()):
        loc_index = len(locations)
        location_id_lookup[node_id] = loc_index
        loc_data = coords[node_id]
        locations.append(Location(location_id=loc_index, x=loc_data["x"], y=loc_data["y"]))

    depot = Depot(
        location_id=location_id_lookup[depot_node_id],
        x=coords[depot_node_id]["x"],
        y=coords[depot_node_id]["y"],
    )

    customers = []
    for node_id in sorted(coords.keys()):
        if node_id == depot_node_id:
            continue
        if node_id not in demands:
            raise ValueError(f"Missing demand for customer {node_id}")
        customers.append(Customer(
            customer_id=len(customers),
            location_id=location_id_lookup[node_id],
            x=coords[node_id]["x"],
            y=coords[node_id]["y"],
            demand=demands[node_id],
        ))

    distance_matrix = compute_distance_matrix(locations)

    instance = CvrpInstance(
        instance_uid=f"CVRPLIB(dist-mat)/{set_name}/{file_path.stem}",
        origin=f"{zip_url} - CVRP benchmark instance from {set_name}",
        vehicle_capacity=vehicle_capacity,
        depot=depot,
        locations=locations,
        customers=customers,
        num_customers=len(customers),
        distance_matrix=distance_matrix,
        schema_version=0,
    )

    connector.upload_instance(instance)

if __name__ == "__main__":
    connector = Connector(
        base_url=os.environ.get("BASE_URL", "http://127.0.0.1"),
        problem_uid=os.environ.get("PROBLEM_UID", PROBLEM_UID),
        api_key=os.environ.get("API_KEY", "your-api-key"),
    )

    extract_root = Path("data/cvrp_benchmarks")

    for zip_url in CVRP_ZIP_URLS:
        try:
            extract_dir, set_name = download_and_extract_cvrp_zip(zip_url, extract_root)
            for file_path in extract_dir.rglob("*.vrp"):
                try:
                    logger.info(f"Processing {file_path.name} from {set_name}")
                    parse_cvrp(file_path, connector, set_name, zip_url)
                except Exception as e:
                    logger.error(f"ERROR processing {file_path.name}: {e}")
        except Exception as e:
            logger.error(f"ERROR with {zip_url}: {e}")

    logger.info("All CVRP benchmark sets processed.")
