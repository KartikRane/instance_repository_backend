import logging

from typing import Type
import sqlmodel
from sqlmodel.main import SQLModelMetaclass

from .problem_info import ProblemInfo


def _generate_problem_instance_index_table(
    problem_info: ProblemInfo,
) -> Type[sqlmodel.SQLModel]:
    """
    Creates a SQLModel class that represents the index table for the instances of the problem.
    It is automatically generated based on the information provided in the problem_info parameter.
    """
    annotations = {}
    class_name = f"{problem_info.problem_uid.replace('-', '_')}_instances"
    class_dict = {
        "__tablename__": class_name,
    }
    logging.debug(
        "Generating index table class with name=%s for problem_uid=%s",
        class_name,
        problem_info.problem_uid,
    )

    # Create index field
    uid_attribute = problem_info.uid_attribute
    annotations[uid_attribute] = problem_info.instance_model.__annotations__[
        uid_attribute
    ]
    class_dict[uid_attribute] = sqlmodel.Field(
        ..., primary_key=True, description="The unique identifier of the instance"
    )
    logging.info(
        "Added primary key field '%s' to the index table for problem_uid=%s",
        uid_attribute,
        problem_info.problem_uid,
    )

    # Create other fields
    for field_name in set(
        problem_info.range_filters
        + problem_info.boolean_filters
        + problem_info.sort_fields
        + problem_info.display_fields
    ) - {uid_attribute}:
        annotations[field_name] = problem_info.instance_model.__annotations__[
            field_name
        ]
        class_dict[field_name] = sqlmodel.Field(
            ...,
            description=problem_info.instance_model.model_fields[
                field_name
            ].description,
        )
        logging.info(
            "Added field '%s' to the index table for problem_uid=%s",
            field_name,
            problem_info.problem_uid,
        )

    class_dict["__annotations__"] = annotations  # type: ignore

    # Use the SQLModel metaclass to create the class and pass table=True
    model_class = SQLModelMetaclass(
        class_name, (sqlmodel.SQLModel,), class_dict, table=True
    )
    logging.debug(
        "Index table class '%s' created successfully for problem_uid=%s",
        class_name,
        problem_info.problem_uid,
    )
    return model_class  # type: ignore
