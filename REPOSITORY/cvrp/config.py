from pydantic import BaseModel, Field, PositiveInt
from typing import Optional

class CvrpInstance(BaseModel):
    """
    Pydantic model representing a Capacitated Vehicle Routing Problem (CVRP) instance.
    """

    # Metadata
    instance_uid: str = Field(..., description="Unique identifier of the instance.")
    origin: str = Field(default="", description="Origin or source of the instance.")

    # Raw instance data
    vehicle_capacity: PositiveInt = Field(
        ..., description="Maximum capacity of each vehicle."
    )
    depot: tuple[float, float] = Field(
        ..., description="Coordinates (x, y) of the depot."
    )
    customers: list[tuple[float, float]] = Field(
        ..., description="List of customer coordinates (x, y)."
    )
    demands: list[PositiveInt] = Field(
        ..., description="Demand for each customer (matches order of customers)."
    )
    distance_matrix: list[list[float]] = Field(
        ..., description="Distance matrix including depot and customers."
    )


class CvrpSolution(BaseModel):
    """
    Pydantic model representing a solution to a CVRP instance.
    """

    instance_uid: str = Field(
        ..., description="The unique identifier of the corresponding instance."
    )
    tours: list[list[int]] = Field(
        ...,
        description="List of vehicle tours. Each tour is a list of customer indices (0-based)."
    )
    objective: Optional[float] = Field(
        None, description="Total distance traveled in the solution."
    )
    authors: Optional[str] = Field(
        None, description="The authors or contributors of the solution."
    )


# Configuration constants for the CVRP

PROBLEM_UID = "cvrp"
INSTANCE_UID_ATTRIBUTE = "instance_uid"

INSTANCE_SCHEMA = CvrpInstance
SOLUTION_SCHEMA = CvrpSolution

RANGE_FILTERS = ["vehicle_capacity"]
BOOLEAN_FILTERS = []
SORT_FIELDS = ["vehicle_capacity"]

DISPLAY_FIELDS = [
    "instance_uid",
    "vehicle_capacity",
    "origin",
]

ASSETS = {"thumbnail": "png", "image": "png"}

SOLUTION_SORT_ATTRIBUTES = ["objective", "authors"]
SOLUTION_DISPLAY_FIELDS = ["objective", "authors"]

