from pydantic import BaseModel, Field, PositiveInt
from typing import Optional


class Cvrp2DCustomer(BaseModel):
    """Represents a customer in the 2D CVRP."""
    customer_id: int = Field(..., description="Customer ID (starting from 1).")
    x: float = Field(..., description="X coordinate of the customer.")
    y: float = Field(..., description="Y coordinate of the customer.")
    demand: PositiveInt = Field(..., description="Demand of the customer.")


class Cvrp2DInstance(BaseModel):
    """Simplified CVRP instance focusing only on customer locations and demands."""
    instance_uid: str = Field(..., description="Unique identifier for the instance.")
    origin: str = Field(default="", description="Benchmark or dataset source.")
    customers: list[Cvrp2DCustomer] = Field(..., description="List of customer data (location and demand).")


# Configuration constants for CVRP_2D

PROBLEM_UID = "cvrp_2d"
INSTANCE_UID_ATTRIBUTE = "instance_uid"

INSTANCE_SCHEMA = Cvrp2DInstance
SOLUTION_SCHEMA = None  # Not defined yet

RANGE_FILTERS = []
BOOLEAN_FILTERS = []
SORT_FIELDS = ["instance_uid"]

DISPLAY_FIELDS = [
    "instance_uid",
    "origin",
]

ASSETS = {"thumbnail": "png", "image": "png"}

SOLUTION_SORT_ATTRIBUTES = []
SOLUTION_DISPLAY_FIELDS = []
