import os
import json
import lzma
import urllib.request
from zipfile import ZipFile
from pathlib import Path
import logging
from config import PickupAndDeliveryInstance, Depot, Location, Request, PROBLEM_UID
from connector import Connector 

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ZIP source(s)
PICKUP_AND_DELIVERY_ZIP_URLS = [
    "https://prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com/wr2ct4r22f-2.zip"
]


def download_and_extract_zip(zip_url: str, extract_root: Path):
    zip_name = "pickup_and_delivery.zip"
    set_name = "pickup_and_delivery"
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


def parse_instance_file(file_path: str, set_name: str, zip_url: str) -> PickupAndDeliveryInstance:
    file_path = Path(file_path) # Ensuring file_path is a Path object
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    metadata = {}
    nodes = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith("NAME:"):
            metadata["instance_uid"] = line.split(":", 1)[1].strip()
        elif line.startswith("LOCATION:"):
            metadata["city"] = line.split(":", 1)[1].strip()
        elif line.startswith("COMMENT:"):
            metadata["origin"] = line.split(":", 1)[1].strip()
        elif line.startswith("SIZE:"):
            metadata["size"] = int(line.split(":", 1)[1].strip())
        elif line.startswith("DISTRIBUTION:"):
            metadata["distribution"] = line.split(":", 1)[1].strip()
        elif line.startswith("DEPOT:"):
            metadata["depot_type"] = line.split(":", 1)[1].strip()
        elif line.startswith("ROUTE-TIME:"):
            metadata["horizon"] = float(line.split(":", 1)[1].strip())
        elif line.startswith("TIME-WINDOW:"):
            metadata["time_window"] = float(line.split(":", 1)[1].strip())
        elif line.startswith("CAPACITY:"):
            metadata["capacity"] = int(line.split(":", 1)[1].strip())
        elif line == "NODES":
            i += 1
            while i < len(lines) and not lines[i].startswith("EDGES"):
                tokens = lines[i].split()
                if len(tokens) < 7:
                    raise ValueError(f"Invalid node format: {lines[i]}")
                node_id = int(tokens[0])
                x = float(tokens[1])
                y = float(tokens[2])
                demand = int(tokens[3])
                ready_time = float(tokens[4])
                due_time = float(tokens[5])
                service_time = float(tokens[6])
                nodes.append((node_id, x, y, demand, ready_time, due_time, service_time))
                i += 1
        i += 1

    if not nodes:
        raise ValueError(f"No valid node data found in {file_path}")

    depot_data = nodes[0]
    depot = Depot(
        x=depot_data[1],
        y=depot_data[2],
        ready_time=depot_data[4],
        due_time=depot_data[5],
        service_time=depot_data[6]
    )

    requests = []
    for idx in range(1, len(nodes), 2):
        if idx + 1 >= len(nodes):
            raise IndexError("Mismatched pickup and delivery pairs.")

        pickup_data = nodes[idx]
        delivery_data = nodes[idx + 1]

        pickup_location = Location(
            x=pickup_data[1],
            y=pickup_data[2],
            ready_time=pickup_data[4],
            due_time=pickup_data[5],
            service_time=pickup_data[6]
        )

        delivery_location = Location(
            x=delivery_data[1],
            y=delivery_data[2],
            ready_time=delivery_data[4],
            due_time=delivery_data[5],
            service_time=delivery_data[6]
        )

        request = Request(
            request_id=idx // 2,
            pickup=pickup_location,
            delivery=delivery_location,
            demand=abs(pickup_data[3])
        )
        requests.append(request)

    instance = PickupAndDeliveryInstance(
        instance_uid=f"PUDEL/{set_name}/{file_path.stem}",
        origin=(
             "Sulzbach Sartori, Carlo; Buriol, Luciana (2020), "
             "Instances for the Pickup and Delivery Problem with Time Windows based on open data, "
             "Mendeley Data, V2, doi: 10.17632/wr2ct4r22f.2"
             f"{zip_url} - pickup and delivery benchmark instance (all files including instances as well as solutions)"
             ),
        size=metadata["size"],
        city=metadata["city"],
        distribution=metadata["distribution"],
        clusters=None,
        density=None,
        horizon=metadata["horizon"],
        time_window=metadata["time_window"],
        service_time=depot.service_time,
        capacity=metadata["capacity"],
        depot_type=metadata["depot_type"],
        depot=depot,
        requests=requests
    )

    return instance


if __name__ == "__main__":
    connector = Connector(
        base_url=os.environ.get("BASE_URL", "http://127.0.0.1"),
        problem_uid=os.environ.get("PROBLEM_UID", PROBLEM_UID),
        api_key=os.environ.get("API_KEY", "3456345-456-456"),
    )

    extract_root = Path("data/pickup_and_delivery_raw")

    for zip_url in PICKUP_AND_DELIVERY_ZIP_URLS:
        try:
            extract_dir, set_name = download_and_extract_zip(zip_url, extract_root)

            instances_dir = extract_dir / "Instances"
            if not instances_dir.exists():
                logger.error(f"Instances directory not found: {instances_dir}")
                continue

            nested_extract_dir = extract_dir / "tmp_extracted_instances"
            nested_extract_dir.mkdir(parents=True, exist_ok=True)

            for sub_zip in instances_dir.glob("*.zip"):
                try:
                    logger.info(f"Extracting nested ZIP: {sub_zip.name}")
                    with ZipFile(sub_zip, "r") as zip_ref:
                        zip_ref.extractall(nested_extract_dir)
                except Exception as e:
                    logger.error(f"Failed to extract {sub_zip.name}: {e}")

            for file_path in nested_extract_dir.rglob("*.txt"):
                if file_path.name.lower() in {"readme.txt", "configurations.txt"}:
                    logger.info(f"Skipping non-instance file: {file_path.name}")
                    continue
                try:
                    logger.info(f"Processing {file_path.name}")
                    instance = parse_instance_file(str(file_path), set_name=set_name, zip_url=zip_url)
                    connector.upload_instance(instance)
                    logger.info(f"Uploaded instance: {instance.instance_uid}")
                except Exception as e:
                    logger.error(f"Failed to process {file_path.name}: {e}")
        except Exception as e:
            logger.error(f"Failed to handle ZIP from {zip_url}: {e}")

    logger.info("Finished processing Pickup & Delivery instances.")
