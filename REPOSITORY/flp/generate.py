import json
import lzma
import urllib.request
from pathlib import Path

from config import (
    FLP_URL,
    FLP_DATA_PATH,
    FLP_OUTPUT_DIR,
    FlpInstance,
    CostMatrix,
)

def download_flp_file():
    if not FLP_DATA_PATH.exists():
        print(f"Downloading FLP benchmark from {FLP_URL}")
        FLP_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(FLP_URL, FLP_DATA_PATH)

def parse_flp_file(file_path: Path) -> FlpInstance:
    with open(file_path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    instance_uid = file_path.stem

    num_customers = int(lines[0])
    num_facilities = int(lines[1])

    i = 2
    i += num_facilities  # skip facility capacity and fixed cost
    i += num_customers   # skip customer demand

    def extract_matrix(start_idx):
        flat = list(map(int, lines[start_idx:start_idx + num_customers * num_facilities]))
        matrix = [
            flat[row * num_facilities:(row + 1) * num_facilities]
            for row in range(num_customers)
        ]
        return matrix

    aij = extract_matrix(i)
    i += num_customers * num_facilities

    bij = extract_matrix(i)
    i += num_customers * num_facilities

    cij = extract_matrix(i)

    return FlpInstance(
        instance_uid=instance_uid,
        origin="ORLIB / Beasley (1993)",
        num_customers=num_customers,
        num_facilities=num_facilities,
        costs=CostMatrix(aij=aij, bij=bij, cij=cij)
    )

def save_as_json_xz(instance: FlpInstance, output_path: Path):
    FLP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with lzma.open(output_path, "wt") as f:
        json.dump(instance.dict(), f, indent=2)

def main():
    download_flp_file()
    instance = parse_flp_file(FLP_DATA_PATH)
    output_path = FLP_OUTPUT_DIR / f"{FLP_DATA_PATH.stem}.json.xz"
    save_as_json_xz(instance, output_path)
    print(f"✅ Instance saved to {output_path}")

if __name__ == "__main__":
    main()
