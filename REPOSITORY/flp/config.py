from pydantic import BaseModel, Field, PositiveInt
from pathlib import Path

# --- Downloading and extracting benchmark files ---

FLP_URL = "https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/CCNFP10g1a.txt"
FLP_DATA_PATH = Path("data/flp/CCNFP10g1a.txt")
FLP_OUTPUT_DIR = Path("data/flp_json")
FLP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
'''
Note : The benchmarks used in FLP is from OR-Library, which provides uncapacited warhouse locations. That is the reason 
the location co-ordinates and demands are not taken into consideration (for now). Its basically based on cost matrices.
'''

class CostMatrix(BaseModel):
    aij: list[list[int]] = Field(..., description="Variable cost component Aij (per unit flow)")
    bij: list[list[int]] = Field(..., description="Variable cost component Bij (penalty or secondary cost)")
    cij: list[list[int]] = Field(..., description="Fixed cost component Cij (for using a facility-customer link)")


class FlpInstance(BaseModel):
    instance_uid: str = Field(..., description="Unique instance ID")
    num_customers: PositiveInt = Field(..., description="Number of customers")
    num_facilities: PositiveInt = Field(..., description="Number of potential facilities")
    costs: CostMatrix = Field(..., description="All cost components (Aij, Bij, Cij)")
    origin: str = Field("ORLIB / Beasley (1993)", description="Benchmark origin")


# --- Metadata ---

PROBLEM_UID = "flp"
INSTANCE_UID_ATTRIBUTE = "instance_uid"

INSTANCE_SCHEMA = FlpInstance

RANGE_FILTERS = ["num_customers", "num_facilities"]
BOOLEAN_FILTERS = []
SORT_FIELDS = ["num_customers", "num_facilities"]

DISPLAY_FIELDS = ["instance_uid", "num_customers", "num_facilities", "origin"]

ASSETS = {} 

SOLUTION_SORT_ATTRIBUTES = []
SOLUTION_DISPLAY_FIELDS = []
