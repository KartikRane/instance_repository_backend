from config import JobShopInstance
import lzma
from pathlib import Path
from uuid import uuid4


def write_to_json_xz(data: JobShopInstance):
    """Write a JobShopInstance to a compressed .json.xz file."""
    instance_uid = data.instance_uid
    path = Path(f"./instances/{instance_uid}.json.xz")
    path.parent.mkdir(parents=True, exist_ok=True)
    with lzma.open(path, "wt") as f:
        f.write(data.json())


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

        # Read and skip metadata line
        metadata_line = lines[i].strip()
        i += 1

        # Skip "Times" label if present
        while i < len(lines) and lines[i].strip().lower() == "times":
            i += 1

        if i >= len(lines):
            break

        # Parse Times matrix
        times = []
        while i < len(lines):
            line = lines[i].strip()
            if line == "" or line.lower() == "machines":
                break
            try:
                time_row = [int(x) for x in line.split()]
                times.append(time_row)
            except ValueError:
                print(f"⚠️ Skipping invalid line in times block: {line}")
            i += 1

        # Skip "Machines" label if present
        if i < len(lines) and lines[i].strip().lower() == "machines":
            i += 1

        # Parse Machines matrix
        machines = []
        while i < len(lines):
            line = lines[i].strip()
            if line == "" or line.lower().startswith("nb of jobs"):
                break
            try:
                machine_row = [int(x) for x in line.split()]
                machines.append(machine_row)
            except ValueError:
                print(f"⚠️ Skipping invalid line in machines block: {line}")
            i += 1

        # Create instance if both times and machines were successfully parsed
        if times and machines:
            number_of_jobs = len(times)
            number_of_machines = len(times[0])

            instance = JobShopInstance(
                instance_uid=str(uuid4()),
                origin="tai15_15",
                number_of_jobs=number_of_jobs,
                number_of_machines=number_of_machines,
                times=times,
                machines=machines,
            )

            write_to_json_xz(instance)

        # Skip blank lines before next block
        while i < len(lines) and lines[i].strip() == "":
            i += 1


if __name__ == "__main__":
    parse_tai15_15("./tai15_15.txt")
