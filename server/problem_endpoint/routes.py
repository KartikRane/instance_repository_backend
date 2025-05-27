import logging
from typing import Type
from pydantic import BaseModel
from sqlmodel import Session

from .models import ProblemInfoResponse, PaginatedInstanceResponse

from .security import verify_api_key

from .routes_solutions import build_solution_routes
from .routes_assets import build_asset_routes

from ..database import get_db

from .solution_index import SolutionIndex
from .solution_repository import SolutionRepository

from .asset_repository import AssetRepository
from .problem_info import ProblemInfo
from .instance_index import InstanceIndex
from .instance_repository import InstanceRepository
from fastapi import APIRouter, Depends, FastAPI, HTTPException


def build_routes_for_problem(
    app: FastAPI,
    problem_info: ProblemInfo,
    instance_repository: InstanceRepository,
    instance_index: InstanceIndex,
    solution_repository: SolutionRepository | None,
    solution_index: SolutionIndex | None,
):
    """
    Build API routes for a specific problem.

    Routes include:
    - CRUD operations for instances.
    - Metadata endpoints for instance filtering and schema.
    - Asset management endpoints.
    - Optional solution-specific routes if a solution repository is provided.
    """

    router = APIRouter()
    InstanceModel: Type[BaseModel] = problem_info.instance_model
    QuerySchema: Type[BaseModel] = instance_index.QuerySchema
    asset_repository = AssetRepository(problem_info)

    @router.get("/instances/{instance_uid:path}", response_model=InstanceModel)
    def get_instance(instance_uid: str):
        """
        Retrieve a specific instance by its UID.
        """
        try:
            return instance_repository.read_instance(instance_uid)
        except KeyError as ke:
            raise HTTPException(status_code=404, detail=str(ke))

    @router.get("/instance_info", response_model=PaginatedInstanceResponse)
    def get_instance_infos(
        *,
        session: Session = Depends(get_db),
        query: QuerySchema = Depends(),  # type: ignore
    ):
        """
        Query instance metadata with pagination and filtering support.
        """
        response = instance_index.query(query, session)
        # add assets info
        if problem_info.assets:
            for instance_uid in response.sorted_uids:
                response.assets[instance_uid] = {
                    asset_class: asset_repository.get_url(
                        instance_uid=instance_uid, asset_class=asset_class
                    )
                    for asset_class in asset_repository.available_assets_for_instance(
                        instance_uid
                    )
                }
                response.download_links[instance_uid] = (
                    instance_repository.get_download_url(instance_uid)
                )
        return response

    @router.get("/instance_schema")
    def get_instance_schema() -> dict:
        """
        Return the JSON schema of the instance model.
        """
        return InstanceModel.model_json_schema()

    @router.get(
        "/instance_info/{instance_uid:path}",
        response_model=dict[str, str | int | float | None],
    )
    def get_instance_info(instance_uid: str, session: Session = Depends(get_db)):
        """
        Retrieve metadata for a specific instance by UID.
        """
        result = instance_index.get_instance_metadata(instance_uid, session)
        if result is None:
            raise HTTPException(status_code=404, detail="Instance not found")
        return result.model_dump()

    @router.get("/problem_info")
    def get_problem_info(*, session: Session = Depends(get_db)) -> ProblemInfoResponse:
        """
        Retrieve metadata about the problem, including filters and asset information.
        """
        range_filters = instance_index.get_range_query_bounds(session)
        return ProblemInfoResponse(
            problem_uid=problem_info.problem_uid,
            range_filters=range_filters,
            boolean_filters=problem_info.boolean_filters,
            sort_fields=problem_info.sort_fields,
            display_fields=problem_info.display_fields,
            assets=problem_info.assets,
        )

    @router.post("/instances")
    def create_instance(
        instance: InstanceModel,  # type: ignore
        session: Session = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """
        Create a new instance and index it for querying.
        """
        instance_repository.write_instance(instance)
        instance_index.index_instance(instance, session)

    @router.delete("/instances/{instance_uid:path}")
    def delete_instance(
        instance_uid: str,
        session: Session = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """
        Delete an instance and its associated data from indices and assets.
        Will also delete associated solutions if a solution repository is available.
        """
        instance_repository.delete_instance(instance_uid)
        instance_index.deindex_instance(instance_uid, session)
        asset_repository.delete_assets(instance_uid)
        if solution_index is not None:
            solution_index.deindex_all_solutions_of_instance(instance_uid, session)
        if solution_repository is not None:
            for solution_uid in solution_repository.list_solution_uids_of_instance(
                instance_uid
            ):
                solution_repository.delete_solution(solution_uid)

    build_asset_routes(
        router=router, problem_info=problem_info, asset_repository=asset_repository
    )

    if solution_repository is not None:
        if solution_index is None:
            raise ValueError(
                "Solution index is required when a solution repository is provided"
            )
        build_solution_routes(
            router,
            problem_info=problem_info,
            instance_index=instance_index,
            solution_repository=solution_repository,
            solution_index=solution_index,
        )

    else:
        logging.info("No solution model found. Skipping the solution routes")

    app.include_router(
        router,
        prefix=f"/{problem_info.problem_uid}",
        tags=[problem_info.problem_uid],
    )
