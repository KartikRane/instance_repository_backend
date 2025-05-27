import logging
from typing import Type
from pydantic import BaseModel
from sqlmodel import Session

from .security import verify_api_key

from ..database import get_db

from .solution_index import SolutionIndex
from .solution_repository import SolutionRepository

from .problem_info import ProblemInfo
from .instance_index import InstanceIndex
from fastapi import APIRouter, Depends, HTTPException
from .models import PaginatedRequest


def build_solution_routes(
    router: APIRouter,
    problem_info: ProblemInfo,
    instance_index: InstanceIndex,
    solution_repository: SolutionRepository,
    solution_index: SolutionIndex,
):
    assert problem_info.solution_model is not None, "Solution model should not be None"
    logging.info("Building routes for solutions")
    SolutionModel: Type[BaseModel] = problem_info.solution_model
    assert solution_index is not None, "The solution index should not be None"

    @router.get("/solutions/{solution_uid:path}", response_model=SolutionModel)
    def get_solution(solution_uid: str):
        """
        Retrieve a specific solution by its UID.
        """
        try:
            return solution_repository.read_solution(solution_uid)
        except KeyError as ke:
            logging.error(f"Solution {solution_uid} not found: {ke}")
            raise HTTPException(status_code=404, detail=str(ke))

    @router.get(
        "/solution_info/{instance_uid}",
        response_model=solution_index.PaginatedResponse,
    )
    def get_solution_info(
        instance_uid: str,
        request: PaginatedRequest = Depends(),
        session: Session = Depends(get_db),
    ):
        """
        Retrieve paginated solution metadata for a specific instance.

        Parameters:
        - instance_uid: The unique identifier of the instance.
        - request: Pagination parameters (offset and limit).
        """
        try:
            return solution_index.query(
                session, instance_uid, offset=request.offset, limit=request.limit
            )
        except KeyError as ke:
            raise HTTPException(status_code=404, detail=str(ke))

    @router.get("/solution_schema")
    def get_solution_schema() -> dict:
        """
        Retrieve the JSON schema of the solution model.
        """
        return SolutionModel.model_json_schema()

    @router.post("/solutions")
    def create_solution(
        solution: SolutionModel,  # type: ignore
        session: Session = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """
        Enter a new solution for a specific instance.

        The solution must reference to a valid instance UID.
        """
        instance_uid = getattr(solution, problem_info.uid_attribute)
        if not instance_index.exists(instance_uid, session=session):
            raise HTTPException(status_code=404, detail="Instance not found")
        solution_uid, path = solution_repository.write_solution(solution)
        solution_index.index_solution(
            solution_uid=solution_uid, solution=solution, session=session
        )

    @router.delete("/solutions/{solution_uid:path}")
    def delete_solution(
        solution_uid: str,
        session: Session = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """
        Delete a specific solution by its UID.

        This operation also removes the solution from the index.
        """
        solution_repository.delete_solution(solution_uid)
        solution_index.deindex_solution(solution_uid, session)
