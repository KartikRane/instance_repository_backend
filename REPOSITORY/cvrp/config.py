from pydantic import BaseModel, Field, PositiveInt, NonNegativeInt, model_validator
from typing import Optional


# --- Shared Location Class ---
class Location(BaseModel):
    location_id: int = Field(..., description="Unique ID for this location (used in distance matrix)")
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")

class Customer(Location):
    customer_id: int = Field(..., description="Customer ID")
    demand: NonNegativeInt = Field(..., description="Demand")

class Depot(Location):
    """Depot inherits from Location"""
    pass

class CvrpInstance(BaseModel):

    instance_uid: str = Field(..., description="Unique instance ID")
    origin: str = Field(default="", description="Benchmark or source")
    vehicle_capacity: PositiveInt = Field(..., description="Vehicle capacity")

    locations: list[Location] = Field(..., description="All locations (depot + customers) with unique IDs")
    depot: Depot = Field(..., description="Depot as a full Location model")
    customers: list[Customer] = Field(..., description="List of customer objects")
    num_customers: int = Field(..., description="Number of customers")

    distance_matrix: list[list[float]] = Field(..., description="Distance matrix including depot and customers")
    schema_version: int = Field(default=0, description="Schema version")

    @model_validator(mode="after")
    def validate_instance(self) -> "CvrpInstance":
        num_locations = len(self.locations)
        if len(self.distance_matrix) != num_locations:
            raise ValueError("Distance matrix must match the number of locations (rows).")
        for i, row in enumerate(self.distance_matrix):
            if len(row) != num_locations:
                raise ValueError(f"Distance matrix row {i} must have {num_locations} columns.")
        return self

# --- Solution Schema for CVRP ---
class CvrpSolution(BaseModel):
    instance_uid: str = Field(..., description="Instance this solution belongs to")
    tours: list[list[int]] = Field(
        ..., description="List of tours, each tour is a list of 0-based customer IDs"
    )
    objective: Optional[float] = Field(None, description="Total distance")
    authors: Optional[str] = Field(None, description="Solution contributors")


# --- Config Constants (matching CVRP2D pattern) ---

PROBLEM_UID = "cvrp"
INSTANCE_UID_ATTRIBUTE = "instance_uid"
INSTANCE_SCHEMA = CvrpInstance
SOLUTION_SCHEMA = CvrpSolution

RANGE_FILTERS = ["vehicle_capacity", "num_customers"]
BOOLEAN_FILTERS = []
SORT_FIELDS = ["vehicle_capacity", "num_customers"]

DISPLAY_FIELDS = ["instance_uid", "vehicle_capacity", "origin"]
ASSETS = {"thumbnail": "png", "image": "png"}

SOLUTION_SORT_ATTRIBUTES = ["objective", "authors"]
SOLUTION_DISPLAY_FIELDS = ["objective", "authors"]
