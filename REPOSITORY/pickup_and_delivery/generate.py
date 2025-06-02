import os
import json
import lzma
import urllib.request
import logging
from zipfile import ZipFile
from pathlib import Path
from config import PickupAndDeliveryInstance, Depot, Location, Request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Static URL from Mendeley (renamed locally since it’s served as "file_downloaded")
PICKUP_AND_DELIVERY_ZIP_URLS = [
    "https://data.mendeley.com/public-files/datasets/wr2ct4r22f/2/files/3a7ae280-6b8a-43ab-81d9-639db92169b8/file_downloaded"
]

def download_and_extract_zip(zip_url: str, extract_root: Path):
    zip_name = "pickup_and_delivery.zip"
    set_name = "pickup_and_delivery"
    zip_path = extract_root / zip_name
    extract_dir = extract_root / set_name

    if not zip_path.exists():
        logger.info(f"Downloading {zip_name} from {zip_url}")
        extract_root.mkdir(parents=True, exist_ok=True)
        try:
            req = urllib.request.Request(
                zip_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as out_file:
                out_file.write(response.read())
        except Exception as e:
            raise RuntimeError(f"Download failed: {e}")

    if not extract_dir.exists():
        logger.info(f"Extracting {zip_path} to {extract_dir}")
        with ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

    return extract_dir, set_name


def parse_instance_file(file_path: str) -> PickupAndDeliveryInstance:
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

    return PickupAndDeliveryInstance(
        instance_uid=metadata["instance_uid"],
        origin=metadata["origin"],
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

def save_as_json_xz(instance: PickupAndDeliveryInstance, output_path: Path):
    with lzma.open(output_path, "wt") as f:
        json.dump(instance.model_dump(), f, indent=2)

def main():
    extract_root = Path("data/pickup_and_delivery_raw")
    output_root = Path("data/pickup_and_delivery_parsed")
    output_root.mkdir(parents=True, exist_ok=True)

    for zip_url in PICKUP_AND_DELIVERY_ZIP_URLS:
        try:
            extract_dir, set_name = download_and_extract_zip(zip_url, extract_root)
            for file_path in extract_dir.glob("*.txt"):
                try:
                    logger.info(f"Processing {file_path.name}")
                    instance = parse_instance_file(str(file_path))
                    output_path = output_root / f"{file_path.stem}.json.xz"
                    save_as_json_xz(instance, output_path)
                except Exception as e:
                    logger.error(f"Failed to process {file_path.name}: {e}")
        except Exception as e:
            logger.error(f"Failed to handle ZIP from {zip_url}: {e}")

    logger.info("Finished processing Pickup & Delivery instances.")

if __name__ == "__main__":
    main()
