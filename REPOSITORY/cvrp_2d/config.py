from pydantic import BaseModel, Field, PositiveInt, NonNegativeInt, model_validator

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


class Cvrp2dInstance(BaseModel):
    instance_uid: str = Field(..., description="Unique instance ID")
    origin: str = Field("", description="Dataset or benchmark source")
    vehicle_capacity: PositiveInt = Field(..., description="Vehicle capacity")
    depot: Depot = Field(..., description="Depot location")
    customers: list[Customer] = Field(..., description="List of customers")
    num_customers: NonNegativeInt = Field(
        ..., description="Total number of customers in the instance."
    )

    schema_version: int = Field(
        default=0,
        description="Schema version of the instance. If the schema changes, this will be incremented.",
    )

    # ---------------------------------------------
    # Additional validation methods
    @model_validator(mode="after")
    def validate_instance(self) -> "Cvrp2dInstance":
        if len(self.customers) != self.num_customers:
            raise ValueError(
                f"Expected {self.num_customers} customers, got {len(self.customers)}"
            )
        # verify that the indices of the customers are sequential starting from 0
        if any(
            customer.customer_id != idx for idx, customer in enumerate(self.customers)
        ):
            raise ValueError("Customer IDs must be sequential starting from 0.")
        return self


# Configuration constants for CVRP_2D

PROBLEM_UID = "cvrp_2d"
INSTANCE_UID_ATTRIBUTE = "instance_uid"

INSTANCE_SCHEMA = Cvrp2dInstance

#   TODO : Not sure for the range and sort filters..what exactly to keep

RANGE_FILTERS = ["vehicle_capacity", "num_customers"]
BOOLEAN_FILTERS = []
SORT_FIELDS = ["vehicle_capacity", "num_customers"]

DISPLAY_FIELDS = ["instance_uid", "num_customers", "vehicle_capacity", "origin"]

ASSETS = {"thumbnail": "png", "image": "png"}

SOLUTION_SORT_ATTRIBUTES = []
SOLUTION_DISPLAY_FIELDS = []