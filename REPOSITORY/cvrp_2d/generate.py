import logging
import os
import lzma
from config import PROBLEM_UID, Cvrp2dInstance, Customer, Depot
from pathlib import Path
import urllib.request
from zipfile import ZipFile
from connector import Connector

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# List of CVRP benchmark ZIP URLs
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


def write_to_json_xz(data: Cvrp2dInstance):
    path = Path(f"./instances/{data.instance_uid}.json.xz")
    path.parent.mkdir(parents=True, exist_ok=True)
    with lzma.open(path, "wt") as f:
        f.write(data.model_dump_json(indent=2))


def parse_cvrp_2d(file_path: str, connector: Connector, set_name: str) -> None:
    file_path = Path(file_path)
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

    instance = Cvrp2dInstance(
        instance_uid=f"CVRPLIB/{set_name}/{file_path.stem}",
        origin=f"{zip_url} - CVRP benchmark instance from {set_name}",
        vehicle_capacity=vehicle_capacity,
        depot=depot,
        customers=customers,
        num_customers=len(customers),
    )

    connector.upload_instance(instance)


if __name__ == "__main__":
    connector = Connector(
        base_url=os.environ.get("BASE_URL", "http://127.0.0.1"),
        problem_uid=os.environ.get("PROBLEM_UID", PROBLEM_UID),
        api_key=os.environ.get("API_KEY", "3456345-456-456"),
    )

    extract_root = Path("data/cvrp2d_benchmarks")

    for zip_url in CVRP_ZIP_URLS:
        try:
            extract_dir, set_name = download_and_extract_cvrp_zip(zip_url, extract_root)
            for file_path in extract_dir.rglob("*.vrp"):
                try:
                    print(f"Processing {file_path.name} from {set_name}")
                    parse_cvrp_2d(str(file_path), connector=connector, set_name=set_name)
                except Exception as e:
                    print(f"ERROR processing {file_path.name}: {e}")
        except Exception as e:
            print(f"ERROR with {zip_url}: {e}")

    print("All CVRP_2D benchmark sets processed.")
