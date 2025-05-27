#!/usr/bin/env python3
"""
populate_knapsack.py

Run-once script to download, parse, and upload Knapsack instances
from the Jooken repository. Environment variables can override defaults.
Potentially extend by further public benchmark repositories.
"""
import os
import sys
from pathlib import Path
import zipfile
import logging
import requests

# Maintain old-style import hack for repository root
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(REPOSITORY_ROOT))

from config import KnapsackInstance
from connector import Connector

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def parse_jooken_instance(instance_name: str, instance_path: Path) -> KnapsackInstance:
    """
    Parse a Jooken .in file into a KnapsackInstance.
    """
    lines = instance_path.read_text().splitlines()
    num_items = int(lines[0])
    values: list[int] = []
    weights: list[int] = []

    for line in lines[1 : 1 + num_items]:
        _, profit_str, weight_str = line.split()
        values.append(int(profit_str))
        weights.append(int(weight_str))

    capacity = int(lines[1 + num_items])
    clean_name = instance_name.replace('.', '-')
    return KnapsackInstance(
        instance_uid=f"jooken/{clean_name}",
        origin=(
            "https://github.com/JorikJooken/knapsackProblemInstances | "
            "A new class of hard problem instances for the 0--1 knapsack problem | "
            "Jooken, Jorik et al. | 2022 European Journal of Operational Research | "
            f"{instance_name}"
        ),
        item_values=values,
        item_weights=weights,
        capacity=capacity,
        integral=True,
        num_items=num_items,
        weight_capacity_ratio=KnapsackInstance.calculate_weight_capacity_ratio(
            weights, capacity
        ),
    )


def download_and_extract_zip(url: str, target_zip: Path, extract_dir: Path) -> None:
    """
    Download ZIP from URL to target_zip and extract to extract_dir.
    Skips steps if paths already exist.
    """
    if not target_zip.exists():
        logger.info("Downloading %s to %s", url, target_zip)
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        target_zip.write_bytes(response.content)
    else:
        logger.info("%s exists, skipping download", target_zip)

    if not extract_dir.exists():
        logger.info("Extracting %s to %s", target_zip, extract_dir)
        with zipfile.ZipFile(target_zip, 'r') as z:
            z.extractall(extract_dir)
    else:
        logger.info("%s exists, skipping extraction", extract_dir)


def find_instance_files(root_dir: Path) -> list[Path]:
    """
    Return all files under root_dir ending with 'test.in'.
    """
    files = list(root_dir.rglob('test.in'))
    logger.info("Found %d instance files", len(files))
    return files


def main() -> None:
    # Configuration via environment variables
    base_url = os.environ.get('BASE_URL', 'http://127.0.0.1')
    problem_uid = os.environ.get('PROBLEM_UID', 'knapsack')
    api_key = os.environ.get('API_KEY', "3456345-456-456")
    zip_url = os.environ.get(
        'ZIP_URL',
        'https://github.com/JorikJooken/knapsackProblemInstances/archive/refs/heads/master.zip',
    )
    work_dir = Path(os.environ.get('WORK_DIR', Path.cwd()))

    zip_path = work_dir / 'jooken_master.zip'
    extract_dir = work_dir / 'jooken_master'

    download_and_extract_zip(zip_url, zip_path, extract_dir)
    instance_files = find_instance_files(extract_dir)

    connector = Connector(
        base_url=base_url,
        problem_uid=problem_uid,
        api_key=api_key,
    )

    for path in instance_files:
        instance_name = path.parent.name
        logger.info("Processing %s", path)
        knapsack_inst = parse_jooken_instance(instance_name, path)
        logger.info(
            "Uploading %s (uid=%s)", instance_name, knapsack_inst.instance_uid
        )
        resp = connector.upload_instance(knapsack_inst)
        logger.info("Response: %s", resp)

    logger.info("Completed uploading %d instances.", len(instance_files))


if __name__ == '__main__':  # noqa: C901
    main()
