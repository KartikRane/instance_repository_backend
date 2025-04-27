'''
Benchmark src: https://data.mendeley.com/datasets/wr2ct4r22f/2
'''

from pydantic import BaseModel, Field, PositiveInt
from typing import Optional


class PickupAndDeliveryLocation(BaseModel):
    """Represents a location for pickup or delivery."""

    location_id: int = Field(..., description="Unique ID of the location (positive integer).")
    x: float = Field(..., description="X coordinate of the location.")
    y: float = Field(..., description="Y coordinate of the location.")
    demand: int = Field(..., description="Demand: positive for pickup, negative for delivery.")
    ready_time: float = Field(..., description="Earliest service time allowed.")
    due_time: float = Field(..., description="Latest service time allowed.")
    service_time: float = Field(..., description="Service duration at this location.")


class PickupAndDeliveryInstance(BaseModel):
    """Represents an instance of the Pickup and Delivery Problem with Time Windows."""

    instance_uid: str = Field(..., description="Unique identifier for the instance.")
    origin: str = Field(..., description="Source or origin of the instance dataset.")
    size: PositiveInt = Field(..., description="Number of pickup/delivery requests (excluding depot).")
    city: str = Field(..., description="City from which the instance data was generated.")
    distribution: str = Field(..., description="Distribution type (e.g., random, clustered, etc.).")
    clusters: Optional[int] = Field(None, description="Number of clusters (if applicable).")
    density: Optional[float] = Field(None, description="Density factor of the locations (if applicable).")
    horizon: float = Field(..., description="Planning horizon (maximum time available).")
    time_window: float = Field(..., description="Width of time windows.")
    service_time: float = Field(..., description="Fixed service time per location.")
    capacity: PositiveInt = Field(..., description="Vehicle capacity.")
    depot_type: str = Field(..., description="Type of depot (e.g., random, central).")

    depot: PickupAndDeliveryLocation = Field(..., description="Depot location details.")
    locations: list[PickupAndDeliveryLocation] = Field(..., description="List of pickup and delivery locations.")


# Configuration constants

PROBLEM_UID = "pickup_and_delivery"
INSTANCE_UID_ATTRIBUTE = "instance_uid"

INSTANCE_SCHEMA = PickupAndDeliveryInstance
SOLUTION_SCHEMA = None  # For now, solution model can be defined later

RANGE_FILTERS = [
    "size",
    "capacity",
    "horizon",
    "time_window",
    "service_time",
    "density",
]

BOOLEAN_FILTERS = []  # No explicit booleans for now

SORT_FIELDS = [
    "size",
    "city",
    "distribution",
]

DISPLAY_FIELDS = [
    "instance_uid",
    "city",
    "distribution",
    "size",
    "horizon",
    "capacity",
    "depot_type",
]

ASSETS = {"thumbnail": "png", "image": "png"}  # Placeholder for potential visualization assets

SOLUTION_SORT_ATTRIBUTES = []  # Empty for now
SOLUTION_DISPLAY_FIELDS = []  # Empty for now
