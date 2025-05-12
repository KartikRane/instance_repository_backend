from pydantic import BaseModel, Field, PositiveInt, conlist
from typing import Optional
import statistics

'''
Benchmark src :
http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/A/A-n32-k5.vrp
'''

class CvrpInstance(BaseModel):
    """
    Pydantic model representing a Capacitated Vehicle Routing Problem (CVRP) instance.
    """

    # Metadata
    instance_uid: str = Field(..., description="The unique identifier of the instance.")
    origin: str = Field(default="", description="The origin or source of the instance.")

    # Instance data
    vehicle_capacity: PositiveInt = Field(..., description="Maximum capacity of each vehicle.")
    depot: tuple[float, float] = Field(..., description="Coordinates (x, y) of the depot.")
    customers: list[tuple[float, float]] = Field(..., description="List of customer coordinates (x, y).")
    demands: list[PositiveInt] = Field(..., description="Demand for each customer (order matches 'customers' list).")

    # Relative attributes
    @property
    def num_customers(self) -> int:
        """Total number of customers (excluding depot)."""
        return len(self.customers)

    @property
    def relative_vehicle_capacity(self) -> float:
        """Ratio of vehicle capacity to total demand."""
        return self.vehicle_capacity / sum(self.demands)

    @property
    def max_mean_customers_per_tour(self) -> float:
        """Maximum number of average customers per vehicle (estimated)."""
        return self.vehicle_capacity / statistics.mean(self.demands)



class CvrpSolution(BaseModel):
    """
    Pydantic model representing a solution to a CVRP instance.
    """
    instance_uid: str = Field(..., description="The unique identifier of the corresponding instance.")
    tours: list[list[int]] = Field(..., description="List of vehicle tours. Each tour is a list of customer indices (0-indexed).")
    objective: Optional[float] = Field(None, description="Total distance traveled in the solution.")
    authors: Optional[str] = Field(None, description="The authors or contributors of the solution.")



# Configuration constants for the CVRP

# Unique identifier for the problem
PROBLEM_UID = "cvrp"

# Shared attribute name for instances and solutions
INSTANCE_UID_ATTRIBUTE = "instance_uid"

# Schema definitions
INSTANCE_SCHEMA = CvrpInstance
SOLUTION_SCHEMA = CvrpSolution

# Filtering and sorting configurations
RANGE_FILTERS = [
    "vehicle_capacity",
]  # Fields usable for range filters

BOOLEAN_FILTERS = []  # No boolean fields

SORT_FIELDS = [
    "vehicle_capacity",
]

# Fields for display purposes in instance overviews
DISPLAY_FIELDS = [
    "instance_uid",
    "vehicle_capacity",
    "origin",
]

# Assets associated with the CVRP problem
ASSETS = {"thumbnail": "png", "image": "png"}

# Solution-specific configurations
SOLUTION_SORT_ATTRIBUTES = ["objective", "authors"]
SOLUTION_DISPLAY_FIELDS = ["objective", "authors"]
