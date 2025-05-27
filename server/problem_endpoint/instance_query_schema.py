import logging

from pydantic import BaseModel, Field
from typing import Type


from .problem_info import ProblemInfo


def _generate_query_schema(problem_info: ProblemInfo) -> Type[BaseModel]:
    """
    Generate a query model for the instances of the problem.
    This model can then be used to validate the query parameters of the API endpoint,
    as well as to automatically build the SQL query.
    """
    annotations = {}
    class_name = f"{problem_info.problem_uid.replace('-', '_')}_query"
    class_dict = {}
    logging.debug(
        "Generating query schema class '%s' for problem_uid=%s",
        class_name,
        problem_info.problem_uid,
    )

    # Add the range filters
    for field_name in problem_info.range_filters:
        min_field_name = (
            f"{field_name}{problem_info.postfix_query}{problem_info.postfix_query_geq}"
        )
        max_field_name = (
            f"{field_name}{problem_info.postfix_query}{problem_info.postfix_query_leq}"
        )
        class_dict[min_field_name] = Field(
            default=None,
            description=problem_info.instance_model.model_fields[
                field_name
            ].description,
        )
        annotations[min_field_name] = float | None
        class_dict[max_field_name] = Field(
            default=None,
            description=problem_info.instance_model.model_fields[
                field_name
            ].description,
        )
        annotations[max_field_name] = float | None
        logging.debug(
            "Added range filter fields '%s' and '%s' for problem_uid=%s",
            min_field_name,
            max_field_name,
            problem_info.problem_uid,
        )

    # Add the boolean filters
    for field_name in problem_info.boolean_filters:
        field_name_ = f"{field_name}{problem_info.postfix_query}"
        class_dict[field_name_] = Field(
            default=None,
            description=problem_info.instance_model.model_fields[
                field_name
            ].description,
        )
        annotations[field_name_] = bool | None
        logging.debug(
            "Added boolean filter field '%s' for problem_uid=%s",
            field_name_,
            problem_info.problem_uid,
        )

    # Add the sort fields
    assert "sort_by" not in annotations, "`sort_by` is a reserved field name"
    annotations["sort_by"] = str | None
    class_dict["sort_by"] = Field(
        None,
        description=(
            f"The field to sort the instances by. Allowed values: "
            f"{', '.join(problem_info.sort_fields)}, "
            f"{', '.join(['-' + f for f in problem_info.sort_fields])}"
        ),
    )
    logging.debug("Added 'sort_by' field for problem_uid=%s", problem_info.problem_uid)

    # Add the search field
    assert "search" not in annotations, "`search` is a reserved field name"
    class_dict["search"] = Field(
        None, description="A keyword to search for in the instances"
    )
    annotations["search"] = str | None
    logging.debug("Added 'search' field for problem_uid=%s", problem_info.problem_uid)

    # Pagination
    assert "offset" not in annotations, "`offset` is a reserved field name"
    class_dict["offset"] = Field(0, description="The offset of the current page")
    annotations["offset"] = int
    assert "limit" not in annotations, "`limit` is a reserved field name"
    class_dict["limit"] = Field(100, description="The limit of the current page")
    annotations["limit"] = int
    logging.debug(
        "Added pagination fields 'offset' and 'limit' for problem_uid=%s",
        problem_info.problem_uid,
    )

    # Use the Pydantic BaseModel metaclass to create the class
    class_dict["__annotations__"] = annotations
    model_class = type(class_name, (BaseModel,), class_dict)
    logging.info(
        "Query schema class '%s' generated successfully for problem_uid=%s",
        class_name,
        problem_info.problem_uid,
    )
    return model_class
