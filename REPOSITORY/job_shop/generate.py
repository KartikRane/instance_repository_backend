from job_shop_config import JobShopInstance
import lzma
from pathlib import Path
from uuid import uuid4


def write_to_json_xz(data: JobShopInstance):
    """Write a JobShopInstance to a compressed .json.xz file."""
    instance_uid = data.instance_uid
    path = Path(f"./instances/{instance_uid}.json.xz")
    path.parent.mkdir(parents=True, exist_ok=True)
    with lzma.open(path, "wt") as f:
        f.write(data.model_dump_json())


def parse_tai15_15(file_path: str):
    """Parse the tai15_15.txt file and convert instances to JobShopInstance objects."""
    with open(file_path, "r") as file:
        lines = file.readlines()

    i = 0
    while i < len(lines):
        # Skip empty lines
        if lines[i].strip() == "":
            i += 1
            continue

        # Read metadata (but ignore them later)
        metadata_line = lines[i]
        i += 1

        if i >= len(lines):
            break

        # Parse Times matrix
        times = []
        while i < len(lines) and lines[i].strip() != "" and not lines[i].startswith("Machines"):
            time_row = [int(x) for x in lines[i].strip().split()]
            times.append(time_row)
            i += 1

        # Skip the "Machines" label
        if i < len(lines) and lines[i].strip() == "Machines":
            i += 1

        # Parse Machines matrix
        machines = []
        while i < len(lines) and lines[i].strip() != "" and not lines[i].startswith("Nb of jobs"):
            machine_row = [int(x) for x in lines[i].strip().split()]
            machines.append(machine_row)
            i += 1

        # Create instance
        number_of_jobs = len(times)
        number_of_machines = len(times[0]) if times else 0

        instance = JobShopInstance(
            instance_uid=str(uuid4()),
            origin="tai15_15",
            number_of_jobs=number_of_jobs,
            number_of_machines=number_of_machines,
            times=times,
            machines=machines,
        )

        # Save instance
        write_to_json_xz(instance)

        # After machines block, skip to next block (if any)
        while i < len(lines) and lines[i].strip() == "":
            i += 1


if __name__ == "__main__":
    parse_tai15_15("./tai15_15.txt")
