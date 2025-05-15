# Import necessary classes from config
from config import PickupAndDeliveryInstance, PickupAndDeliveryLocation

# Import libraries for compression, file handling, and unique ID generation
import lzma
from pathlib import Path
from uuid import uuid4
import csv

# --------------------------------------
# Function to write instance to JSON.xz
# --------------------------------------


def write_to_json_xz(data: PickupAndDeliveryInstance):
    """Write a PickupAndDeliveryInstance to a compressed JSON (.json.xz) file."""
    path = Path(f"./instances/{data.instance_uid}.json.xz")
    path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
    with lzma.open(path, "wt") as f:
        f.write(
            data.model_dump_json(indent=2)
        )  # Save formatted JSON into compressed file


# --------------------------------------
# Function to parse a .txt file into an instance
# --------------------------------------


def parse_instance_file(filepath: Path, config_row: dict) -> PickupAndDeliveryInstance:
    """Parse a single PDPTW instance .txt file into PickupAndDeliveryInstance format."""
    with filepath.open("r") as f:
        lines = f.readlines()

    locations = []  # List to store all pickup and delivery locations
    depot = None  # Depot location
    reading_locations = False  # Flag to know when reading location section starts

    for line in lines:
        line = line.strip()

        # Start reading location information when NODE_COORD_SECTION or PICKUP_SECTION appears
        if line.startswith("NODE_COORD_SECTION") or line.startswith("PICKUP_SECTION"):
            reading_locations = True
            continue

        # Stop reading at EOF marker
        if line == "EOF":
            break

        if reading_locations:
            parts = line.split()
            if len(parts) < 7:
                continue  # Skip any incomplete lines

            # Extract location details
            location_id = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            demand = int(parts[3])
            ready_time = float(parts[4])
            due_time = float(parts[5])
            service_time = float(parts[6])

            # Create a PickupAndDeliveryLocation object
            loc = PickupAndDeliveryLocation(
                location_id=location_id,
                x=x,
                y=y,
                demand=demand,
                ready_time=ready_time,
                due_time=due_time,
                service_time=service_time,
            )

            # Identify depot separately (location_id = 0)
            if location_id == 0:
                depot = loc
            else:
                locations.append(loc)

    # Ensure depot is found
    if depot is None:
        raise ValueError(f"Depot not found in {filepath}")

    # Create the full instance object
    instance = PickupAndDeliveryInstance(
        instance_uid=f"pickup_delivery_{uuid4().hex[:8]}",  # Unique ID
        origin="PDPTW Mendeley Dataset",  # Hardcoded origin
        size=int(config_row["Size"]),
        city=config_row["City"],
        distribution=config_row["Distribution"],
        clusters=int(config_row["Clusters"]) if config_row["Clusters"] != "-" else None,
        density=float(config_row["Density"]) if config_row["Density"] != "-" else None,
        horizon=float(config_row["Horizon"]),
        time_window=float(config_row["Time Window"]),
        service_time=float(config_row["Service Time"]),
        capacity=int(config_row["Capacity"]),
        depot_type=config_row["Depot"],
        depot=depot,
        locations=locations,
    )

    return instance


# --------------------------------------
# Main execution block
# --------------------------------------

if __name__ == "__main__":
    config_path = Path("./configurations.txt")  # Path to the configurations metadata
    instances_folder = Path("./Instances")  # Folder containing all .txt instance files

    # Read the configurations file
    with config_path.open("r") as f:
        reader = csv.DictReader(f, delimiter=";")
        configs = list(reader)

    # Loop over all configuration rows
    for config_row in configs:
        instance_filename = config_row["Name"] + ".txt"
        instance_path = instances_folder / instance_filename

        # Skip missing files
        if not instance_path.exists():
            print(f"Warning: {instance_path} does not exist. Skipping.")
            continue

        # Parse the file and write to compressed JSON
        instance = parse_instance_file(instance_path, config_row)
        write_to_json_xz(instance)

    print(" All instances processed.")
