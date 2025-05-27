import lzma
import os
from pathlib import Path
from uuid import uuid4
import urllib.request

# Maintain old-style import hack for repository root
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(REPOSITORY_ROOT))

from config import (
    JobShopInstance,
    Job,
    Operation,
    Machine,
    JOBSHOP_BENCHMARK_URLS,
    JOBSHOP_DOWNLOAD_DIR,
)
from connector import Connector

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# The job shop benchmark library does not have a zip folder so the download is done via the links provided below.
# New links can be added according to the requirement.

# Mapping of job shop instance filenames to their respective URLs
JOBSHOP_BENCHMARK_URLS = {
    "tai15_15.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai15_15.txt",
    "tai20_15.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai20_15.txt",
    "tai20_20.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai20_20.txt",
    "tai30_15.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai30_15.txt",
    "tai30_20.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai30_20.txt",
    "tai50_15.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai50_15.txt",
    "tai50_20.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai50_20.txt",
    "tai100_20.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai100_20.txt",
}

# Target directory where benchmark files will be downloaded
JOBSHOP_DOWNLOAD_DIR = Path("benchmark_instances")

def download_missing_files():
    """
    Downloads all Job Shop benchmark files if they do not exist locally.
    """
    JOBSHOP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in JOBSHOP_BENCHMARK_URLS.items():
        local_path = JOBSHOP_DOWNLOAD_DIR / filename
        if not local_path.exists():
            print(f" Downloading {filename} from {url}")
            urllib.request.urlretrieve(url, local_path)


def write_to_json_xz(instance: JobShopInstance):
    """
    Serializes the JobShopInstance to a compressed JSON (.json.xz) file.
    """
    path = Path(f"./instances/{instance.instance_uid}.json.xz")
    path.parent.mkdir(parents=True, exist_ok=True)
    with lzma.open(path, "wt") as f:
        f.write(instance.model_dump_json(indent=2))


def parse_jobshop_instance(file_path: Path) -> JobShopInstance:
    """
    Parses a Job Shop file and returns a JobShopInstance object.
    """
    with file_path.open("r") as f:
        lines = [line.strip() for line in f if line.strip()]

    i = 0  # Initialize the index variable

    # Skip metadata and the line containing "Times"
    while i < len(lines):
        if lines[i].lower().startswith("times"):
            i += 1
            break
        i += 1

    # Read Times matrix
    times = []
    while i < len(lines) and not lines[i].lower().startswith("machines"):
        try:
            time_row = [int(x) for x in lines[i].split()]
            times.append(time_row)
        except ValueError:
            print(f" Skipping invalid time line: {lines[i]}")
        i += 1

    # Read Machines matrix
    if i < len(lines) and lines[i].lower().startswith("machines"):
        i += 1
    machines = []
    while i < len(lines):
        try:
            machine_row = [int(x) for x in lines[i].split()]
            machines.append(machine_row)
        except ValueError:
            print(f" Skipping invalid machine line: {lines[i]}")
        i += 1

    number_of_jobs = len(times)
    number_of_machines = len(times[0]) if times else 0

    # Build machine objects
    machine_objs = [
        Machine(machine_id=m_id, name=f"Machine {m_id}")
        for m_id in range(1, number_of_machines + 1)
    ]

    # Build jobs with operations
    jobs = []
    for job_id in range(1, number_of_jobs + 1):
        ops = []
        for op_index in range(number_of_machines):
            machine_id = machines[job_id - 1][op_index]
            processing_time = times[job_id - 1][op_index]
            ops.append(
                Operation(machine_id=machine_id, processing_time=processing_time)
            )
        jobs.append(Job(job_id=job_id, operations=ops))

    instance = JobShopInstance(
        instance_uid=f"OR-Library/{file_path.stem}",
        origin=("https://people.brunel.ac.uk/~mastjjb/jeb/orlib/jobshopinfo.html"
                "OR-Library is a collection of test data sets for a variety of OR problems."),
        machines=machine_objs,
        jobs=jobs,
        number_of_jobs=number_of_jobs,
        number_of_machines=number_of_machines,
    )


    return instance


if __name__ == "__main__":
    # Configuration via environment variables
    base_url = os.environ.get('BASE_URL', 'http://127.0.0.1')
    problem_uid = os.environ.get('PROBLEM_UID', 'job_shop')
    api_key = os.environ.get('API_KEY', "3456345-456-456")

    #download benchmark files if not present
    download_missing_files()

    connector = Connector(
        base_url=base_url,
        problem_uid=problem_uid,
        api_key=api_key,
    )

    for file_path in JOBSHOP_DOWNLOAD_DIR.glob("*.txt"):
        try:
            print(f"-----Processing: {file_path.name}---------")
            instance = parse_jobshop_instance(file_path)
            logger.info("Uploading %s (uid=%s)", instance, instance.instance_uid)
            resp = connector.upload_instance(instance)
            logger.info("Response: %s", resp)
            write_to_json_xz(instance)
        except Exception as e:
                print(f" ERROR !!! in  processing {file_path.name}: {e}")

    print(" All Job Shop instances processed.")
