import os
import json
import lzma
from config import PickupAndDeliveryInstance, Depot, Location, Request
from pathlib import Path

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
        elif line.startswith("TYPE:"):
            pass
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
                node_id = int(tokens[0])
                lat = float(tokens[1])
                lon = float(tokens[2])
                demand = int(tokens[3])
                ready_time = float(tokens[4])
                due_time = float(tokens[5])
                service_time = float(tokens[6])
                nodes.append((node_id, lat, lon, demand, ready_time, due_time, service_time))
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
    # pairing based on order: pickup at odd indices, delivery at even indices
    for idx in range(1, len(nodes), 2):
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

        pickup_demand = pickup_data[3]

        request = Request(
            request_id=idx,
            pickup=pickup_location,
            delivery=delivery_location,
            demand=abs(pickup_demand)
        )
        requests.append(request)

    instance = PickupAndDeliveryInstance(
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

    return instance

def save_as_json_xz(instance: PickupAndDeliveryInstance, output_path: Path):
    with lzma.open(output_path, "wt") as f:
        json.dump(instance.dict(), f, indent=2)

def main():
    input_file = "bar-n1000-5.txt"
    output_file = Path(f"{input_file.replace('.txt', '.json.xz')}")
    instance = parse_instance_file(input_file)
    save_as_json_xz(instance, output_file)
    print(f"Instance saved to {output_file}")

if __name__ == "__main__":
    main()
