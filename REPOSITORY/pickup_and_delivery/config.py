from pydantic import BaseModel, Field, PositiveInt
from typing import Optional

class Location(BaseModel):
    """
    Represents a geographic location with time window and service time constraints.
    """
    x: float = Field(..., description="X coordinate (e.g., longitude).")
    y: float = Field(..., description="Y coordinate (e.g., latitude).")
    ready_time: float = Field(..., description="Earliest allowable service start time at this location.")
    due_time: float = Field(..., description="Latest allowable service start time at this location.")
    service_time: float = Field(..., description="Time required to serve at this location.")

class Depot(Location):
    """
    A Depot is a special location that serves as the start and end point for vehicles.
    Inherits time windows and coordinates from Location.
    """
    pass

class Request(BaseModel):
    """
    A transport request consisting of a pickup and corresponding delivery location.
    Each request has a demand, and both locations must be serviced within time windows.
    """
    request_id: int = Field(..., description="Unique identifier for the request.")
    pickup: Location = Field(..., description="Pickup location details.")
    delivery: Location = Field(..., description="Delivery location details.")
    demand: PositiveInt = Field(..., description="Positive demand associated with the request.")

class PickupAndDeliveryInstance(BaseModel):
    """
    Full definition of a Pickup and Delivery problem instance with time windows (PDP-TW).
    """
    instance_uid: str = Field(..., description="Globally unique identifier for the instance.")
    origin: str = Field(..., description="Data source or origin of this instance.")
    size: PositiveInt = Field(..., description="Number of pickup-delivery pairs.")
    city: str = Field(..., description="City where the problem is based or simulated.")
    distribution: str = Field(..., description="Type of spatial distribution (e.g., 'random', 'clustered').")
    clusters: Optional[int] = Field(None, description="Number of clusters if clustered distribution is used.")
    density: Optional[float] = Field(None, description="Average request density (requests per unit area).")
    horizon: float = Field(..., description="Total time horizon available for servicing all requests.")
    time_window: float = Field(..., description="Maximum length of any time window.")
    service_time: float = Field(..., description="Uniform service time at pickup and delivery locations.")
    capacity: PositiveInt = Field(..., description="Vehicle capacity constraint.")
    depot_type: str = Field(..., description="Type of depot (e.g., 'central', 'distributed').")
    depot: Depot = Field(..., description="Location and timing information for the depot.")
    requests: list[Request] = Field(..., description="List of pickup-delivery requests.")

# Metadata configuration for filtering, sorting, and displaying instances
PROBLEM_UID = "pickup_and_delivery"
INSTANCE_UID_ATTRIBUTE = "instance_uid"
INSTANCE_SCHEMA = PickupAndDeliveryInstance
SOLUTION_SCHEMA = None  # No solution schema defined yet

RANGE_FILTERS = ["size", "capacity", "horizon", "time_window", "service_time", "density"]
BOOLEAN_FILTERS = []
SORT_FIELDS = ["size", "city", "distribution"]
DISPLAY_FIELDS = ["instance_uid", "city", "distribution", "size", "horizon", "capacity", "depot_type"]

ASSETS = {
    "thumbnail": "png",
    "image": "png",
}
