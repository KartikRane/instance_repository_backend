from pydantic import BaseModel, Field, PositiveInt, NonNegativeInt
from pathlib import Path

# --- Schema for CVRP_2D ---

class Location(BaseModel):
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")

class Customer(Location):
    customer_id: int = Field(..., description="Customer ID")
    demand: NonNegativeInt = Field(..., description="Demand")

class Depot(Location):
    """Depot class, extendable for additional attributes."""
    pass


class Cvrp2DInstance(BaseModel):
    instance_uid: str = Field(..., description="Unique instance ID")
    origin: str = Field("", description="Dataset or benchmark source")
    vehicle_capacity: PositiveInt = Field(..., description="Vehicle capacity")
    depot: Depot = Field(..., description="Depot location")
    customers: list[Customer] = Field(..., description="List of customers")


# Configuration constants for CVRP_2D

PROBLEM_UID = "cvrp_2d"
INSTANCE_UID_ATTRIBUTE = "instance_uid"

INSTANCE_SCHEMA = Cvrp2DInstance

#   TODO : Not sure for the range and sort filters..what exactly to keep

RANGE_FILTERS = ["vehicle_capacity"]
BOOLEAN_FILTERS = []
SORT_FIELDS = ["vehicle_capacity"]

DISPLAY_FIELDS = ["instance_uid", "vehicle_capacity", "origin"]

ASSETS = {"thumbnail": "png", "image": "png"}

SOLUTION_SORT_ATTRIBUTES = []
SOLUTION_DISPLAY_FIELDS = []
