from pydantic import BaseModel, Field, PositiveInt, conlist
from typing import Optional


class JobShopInstance(BaseModel):
    """
    Pydantic model representing a Job Shop Scheduling problem instance.
    """

    # Metadata
    instance_uid: str = Field(..., description="The unique identifier of the instance")
    origin: str = Field(default="", description="The origin or source of the instance")

    # Instance data
    number_of_jobs: PositiveInt = Field(
        ..., description="The number of jobs in the instance."
    )
    number_of_machines: PositiveInt = Field(
        ..., description="The number of machines in the instance."
    )
    times: list[conlist(int, min_items=1)] = Field(
        ..., description="Matrix of processing times; each row corresponds to a job and each column to an operation."
    )
    machines: list[conlist(int, min_items=1)] = Field(
        ..., description="Matrix of machine assignments; each row corresponds to a job and each column to the machine index for the corresponding operation."
    )


class JobShopSolution(BaseModel):
    """
    Pydantic model representing a solution to a Job Shop Scheduling problem instance.
    """

    instance_uid: str = Field(
        ..., description="The unique identifier of the corresponding instance."
    )
    makespan: Optional[int] = Field(
        None, description="The total completion time (makespan) of the schedule."
    )
    operation_start_times: Optional[list[list[int]]] = Field(
        None,
        description="Matrix of start times for operations; operation_start_times[job][operation] = start time."
    )
    authors: Optional[str] = Field(
        None, description="The authors or contributors of the solution."
    )


# Configuration constants for the Job Shop Scheduling Problem

# Unique identifier for the problem
PROBLEM_UID = "job_shop"

# Shared attribute name for instances and solutions
INSTANCE_UID_ATTRIBUTE = "instance_uid"

# Schema definitions
INSTANCE_SCHEMA = JobShopInstance
SOLUTION_SCHEMA = JobShopSolution

# Filtering and sorting configurations
RANGE_FILTERS = [
    "number_of_jobs",
    "number_of_machines",
]  # Only real numerical fields left

BOOLEAN_FILTERS = []  # No boolean fields yet

SORT_FIELDS = [
    "number_of_jobs",
    "number_of_machines",
]

# Fields for display purposes in instance overviews
DISPLAY_FIELDS = [
    "instance_uid",
    "number_of_jobs",
    "number_of_machines",
    "origin",
]

# Assets associated with the job shop problem
ASSETS = {"thumbnail": "png", "image": "png"}  # Can add visualizations later

# Solution-specific configurations
SOLUTION_SORT_ATTRIBUTES = ["makespan", "authors"]
SOLUTION_DISPLAY_FIELDS = ["makespan", "authors"]