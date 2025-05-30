from pydantic import BaseModel, Field, PositiveInt, NonNegativeInt, model_validator
from typing import Optional


# --- Shared Location Class ---
class Location(BaseModel):
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")

class Customer(Location):
    customer_id: int = Field(..., description="Customer ID")
    demand: NonNegativeInt = Field(..., description="Demand")

class Depot(Location):
    """Depot class, can be extended later."""

class CvrpInstance(BaseModel):

    instance_uid: str = Field(..., description="Unique instance ID")
    origin: str = Field(default="", description="Benchmark or source")
    vehicle_capacity: PositiveInt = Field(..., description="Vehicle capacity")

    depot: tuple[float, float] = Field(..., description="Depot coordinates (x, y)")
    customers: list[tuple[float, float]] = Field(..., description="Customer coordinates (x, y)")
    demands: list[PositiveInt] = Field(..., description="Demand for each customer")
    distance_matrix: list[list[float]] = Field(..., description="Distance matrix including depot and customers")

    schema_version: int = Field(default=0, description="Schema version")

    @model_validator(mode="after")
    def validate_instance(self) -> "CvrpInstance":
        if len(self.customers) != len(self.demands):
            raise ValueError("Mismatch: customers and demands must be same length.")
        if len(self.distance_matrix) != (1 + len(self.customers)):
            raise ValueError("Distance matrix must include depot + all customers.")
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

RANGE_FILTERS = ["vehicle_capacity", "demands"]
BOOLEAN_FILTERS = []
SORT_FIELDS = ["vehicle_capacity", "demands"]

DISPLAY_FIELDS = ["instance_uid", "vehicle_capacity", "origin"]
ASSETS = {"thumbnail": "png", "image": "png"}

SOLUTION_SORT_ATTRIBUTES = ["objective", "authors"]
SOLUTION_DISPLAY_FIELDS = ["objective", "authors"]
