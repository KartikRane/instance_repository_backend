from typing import Any, Type
from pydantic import BaseModel, Field
from sqlmodel.main import SQLModelMetaclass
import sqlmodel

from .instance_repository import check_uid_pattern
from .problem_info import ProblemInfo
import logging


class SolutionIndex:
    def __init__(self, problem_info: ProblemInfo):
        self.problem_info = problem_info
        self.IndexTable = self._generate_index_table()
        self.PaginatedResponse = self._generate_paginated_response()

    def _generate_index_table(self) -> Type[sqlmodel.SQLModel]:
        """
        Generate the index table for the solution index.
        """
        annotations = {}
        class_name = f"{self.problem_info.problem_uid.replace('-', '_')}_solution_index"
        class_dict = {"__tablename__": class_name}

        # index field
        index_field = self.problem_info.solution_index_field
        annotations[index_field] = str
        class_dict[index_field] = sqlmodel.Field(..., primary_key=True, index=True)

        # instance field
        fields = (
            set(self.problem_info.solution_display_fields)
            | {f.lstrip("-") for f in self.problem_info.solution_sort_by}
            | {self.problem_info.uid_attribute}
        )
        SolutionModel = self.problem_info.solution_model
        assert SolutionModel is not None, "The instance model should not be None"
        for field in fields:
            annotations[field] = self.problem_info.solution_model.__annotations__[field]
            class_dict[field] = sqlmodel.Field(
                ..., description=SolutionModel.model_fields[field].description
            )

        class_dict["__annotations__"] = annotations  # type: ignore

        # create the class
        model_class = SQLModelMetaclass(
            class_name, (sqlmodel.SQLModel,), class_dict, table=True
        )
        return model_class  # type: ignore

    def exists(self, solution_uid: str, session: sqlmodel.Session) -> bool:
        """
        Check if a solution with the given solution_uid exists.
        """
        check_uid_pattern(solution_uid)
        statement = sqlmodel.select(self.IndexTable).where(
            getattr(self.IndexTable, self.problem_info.solution_index_field)
            == solution_uid
        )
        result = session.exec(statement).first()
        return result is not None

    def _generate_paginated_response(self) -> Type[BaseModel]:
        class_name = f"{self.problem_info.problem_uid.replace('-', '_')}_solution_paginated_response"
        class_dict = {
            "items": Field(..., description="The items in the current page"),
            "offset": Field(..., description="The offset of the current page"),
            "limit": Field(..., description="The limit of the current page"),
            "total": Field(..., description="The total number of items"),
        }
        class_annotations = {
            "items": list[self.IndexTable],
            "offset": int,
            "limit": int,
            "total": int,
        }
        class_dict["__annotations__"] = class_annotations
        # create the class
        return type(class_name, (BaseModel,), class_dict)  # type: ignore

    def query(
        self, session: sqlmodel.Session, instance_uid: str, offset: int, limit: int
    ) -> Any:
        """
        Query the solution index for the solutions of the instance with the given instance_uid.
        """
        statement = sqlmodel.select(self.IndexTable).where(
            getattr(self.IndexTable, self.problem_info.uid_attribute) == instance_uid
        )
        statement_total = sqlmodel.select(sqlmodel.func.count()).select_from(
            statement.alias()
        )
        total = session.exec(statement_total).first()
        assert total is not None, "The total count should not be None"
        statement = (
            statement.order_by(*self.problem_info.solution_sort_by)
            .offset(offset)
            .limit(limit)
        )
        items = list(session.exec(statement).all())
        return self.PaginatedResponse(
            items=items, offset=offset, limit=limit, total=total
        )

    def get_solution_metadata(self, solution_uid: str, session: sqlmodel.Session):
        """
        Get the metadata of the solution with the given solution_uid.
        """
        statement = sqlmodel.select(self.IndexTable).where(
            getattr(self.IndexTable, self.problem_info.solution_index_field)
            == solution_uid
        )
        result = session.exec(statement).first()
        return result

    def index_solution(self, solution_uid, solution, session: sqlmodel.Session):
        """
        Index the solution with the given solution_uid.
        """
        solution_dict = solution.dict()
        solution_dict[self.problem_info.solution_index_field] = solution_uid
        session.add(self.IndexTable(**solution_dict))
        session.commit()
        logging.info(f"Indexed solution {solution_uid}")

    def deindex_solution(self, solution_uid: str, session: sqlmodel.Session):
        """
        Deindex the solution with the given solution_uid.
        """
        check_uid_pattern(solution_uid)
        solution_index = session.get(self.IndexTable, solution_uid)
        if solution_index:
            session.delete(solution_index)
            session.commit()
            logging.info(f"Deindexed solution {solution_uid}")

    def deindex_all_solutions_of_instance(
        self, instance_uid, session: sqlmodel.Session
    ):
        """
        Deindex all the solutions of the instance with the given instance_uid.
        """
        statement = sqlmodel.delete(self.IndexTable).where(
            getattr(self.IndexTable, self.problem_info.uid_attribute) == instance_uid
        )
        session.exec(statement)  # type: ignore
        session.commit()
        logging.info(f"Deindexed all solutions of instance {instance_uid}")
