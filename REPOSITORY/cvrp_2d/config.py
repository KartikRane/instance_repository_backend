from pydantic import BaseModel, Field, NonNegativeInt
from pathlib import Path

CVRP_ZIP_URL = "http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/Vrp-Set-A.zip"
CVRP_ZIP_PATH = Path("data/cvrp2d_benchmarks.zip")
CVRP_EXTRACT_DIR = Path("data/cvrp2d_benchmarks")


class Location(BaseModel):
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")


class Depot(Location):
    pass


class Customer(Location):
    customer_id: NonNegativeInt = Field(..., description="Customer ID (1-based)")
    demand: NonNegativeInt = Field(..., description="Demand")


class Cvrp2DInstance(BaseModel):
    instance_uid: str = Field(..., description="Unique instance ID")
    origin: str = Field("", description="Dataset or benchmark source")
    vehicle_capacity: NonNegativeInt = Field(..., description="Vehicle capacity")
    depot: Depot = Field(..., description="Depot location")
    customers: list[Customer] = Field(..., description="List of customers")
    distance_matrix: list[list[float]] = Field(..., description="Distance matrix between depot and customers")


# Configuration constants for CVRP_2D

PROBLEM_UID = "cvrp_2d"
INSTANCE_UID_ATTRIBUTE = "instance_uid"

INSTANCE_SCHEMA = Cvrp2DInstance

RANGE_FILTERS = ["vehicle_capacity"]
BOOLEAN_FILTERS = []
SORT_FIELDS = ["vehicle_capacity"]

DISPLAY_FIELDS = ["instance_uid", "vehicle_capacity", "origin"]

ASSETS = {"thumbnail": "png", "image": "png"}

SOLUTION_SORT_ATTRIBUTES = []
SOLUTION_DISPLAY_FIELDS = []
