from pydantic import BaseModel, Field, PositiveInt
from typing import Optional
from pathlib import Path

# ---------------------------------------TO SPECIFY BENCHMARK LINKS-------------------------------------------------

# The job shop benchmark library does not have a zip folder so the download is done via the links provided below.
# New links can be added according to the requirement.

# Mapping of job shop instance filenames to their respective URLs
JOBSHOP_BENCHMARK_URLS = {
    "tai15_15.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai15_15.txt",
    "tai20_15.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai20_15.txt",
    "tai20_20.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai20_20.txt",
    "tai30_15.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai30_15.txt",
    "tai30_20.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai30_20.txt",
    "tai50_15.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai50_15.txt",
    "tai50_20.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai50_20.txt",
    "tai100_20.txt": "http://mistic.heig-vd.ch/taillard/problemes.dir/ordonnancement.dir/jobshop.dir/tai100_20.txt",
}

# Target directory where benchmark files will be downloaded
JOBSHOP_DOWNLOAD_DIR = Path("benchmark_instances")

# -------------------------------------------------------------------------------------------------------------------


class Machine(BaseModel):
    """
    Represents a machine in the shop.
    """

    machine_id: int = Field(
        ..., description="Unique machine identifier (starting from 1)."
    )
    name: str = Field(..., description="Optional human‐readable name for the machine.")


class Operation(BaseModel):
    """
    A single operation of a job, to be processed on one machine.
    The sequence in which operations appear in the Job.operations list
    defines their technological order.
    """

    machine_id: int = Field(
        ..., description="ID of the machine required for this operation."
    )
    processing_time: PositiveInt = Field(
        ..., description="Time units needed to complete this operation."
    )


class Job(BaseModel):
    """
    A job is an ordered list of operations.
    """

    job_id: int = Field(..., description="Unique job identifier (starting from 1).")
    operations: list[Operation] = Field(
        ..., description="Operations in the order they must be processed."
    )
    release_time: PositiveInt = Field(
        0, description="Earliest start time for this job."
    )


class JobShopInstance(BaseModel):
    """
    Full Job-Shop Problem instance.
    """

    instance_uid: str = Field(
        ..., description="Unique identifier for this problem instance."
    )
    origin: str = Field(
        "", description="Dataset or benchmark source (e.g. ’tai15_15.txt’)."
    )
    machines: list[Machine] = Field(
        ..., description="List of machines available in the shop."
    )
    jobs: list[Job] = Field(..., description="List of jobs to schedule.")

    number_of_jobs: int = Field(
        ..., description="Total number of jobs in the instance."
    )
    number_of_machines: int = Field(
        ..., description="Total number of machines in the instance."
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
        description="Matrix of start times for operations; operation_start_times[job][operation] = start time.",
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
]

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

ASSETS = {"thumbnail": "png", "image": "png"}

# Solution-specific configurations
SOLUTION_SORT_ATTRIBUTES = ["makespan", "authors"]
SOLUTION_DISPLAY_FIELDS = ["makespan", "authors"]
