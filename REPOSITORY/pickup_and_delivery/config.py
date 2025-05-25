from pathlib import Path
from pydantic import BaseModel, Field, PositiveInt
from typing import Optional

# Benchmark src: https://data.mendeley.com/datasets/wr2ct4r22f/2
# --- Benchmark zip source ---
# --- There are 300 instance zip files. A zip link can be set accordingly.

PDPTW_ZIP_URL = "https://data.mendeley.com/public-files/datasets/wr2ct4r22f/files/3a7ae280-6b8a-43ab-81d9-639db92169b8/file_downloaded"
PDPTW_ZIP_PATH = Path("data/pdptw_benchmark.zip")
PDPTW_EXTRACT_DIR = Path("data/pdptw_benchmark")

class Location(BaseModel):
    x: float = Field(..., description="Latitude coordinate.")
    y: float = Field(..., description="Longitude coordinate.")
    ready_time: float = Field(..., description="Earliest start time.")
    due_time: float = Field(..., description="Latest finish time.")
    service_time: float = Field(..., description="Service duration.")

class Depot(Location):
    """Depot location inherits from general Location."""
    pass

class Request(BaseModel):
    request_id: int
    pickup: Location
    delivery: Location
    demand: PositiveInt

class PickupAndDeliveryInstance(BaseModel):
    instance_uid: str
    origin: str
    size: PositiveInt
    city: str
    distribution: str
    clusters: Optional[int]
    density: Optional[float]
    horizon: float
    time_window: float
    service_time: float
    capacity: PositiveInt
    depot_type: str
    depot: Depot
    requests: list[Request]

# Metadata for filtering and display
PROBLEM_UID = "pickup_and_delivery"
INSTANCE_UID_ATTRIBUTE = "instance_uid"
INSTANCE_SCHEMA = PickupAndDeliveryInstance
SOLUTION_SCHEMA = None

RANGE_FILTERS = ["size", "capacity", "horizon", "time_window", "service_time", "density"]
BOOLEAN_FILTERS = []
SORT_FIELDS = ["size", "city", "distribution"]
DISPLAY_FIELDS = ["instance_uid", "city", "distribution", "size", "horizon", "capacity", "depot_type"]
ASSETS = {
    "thumbnail": "png",
    "image": "png",
}

