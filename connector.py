import logging
from typing import Any
from requests import Session
from pydantic import BaseModel

# Configure root logger – adjust level as needed
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class Connector:
    """
    A simple example connector that logs all HTTP calls made, including the URL, parameters, payload, and responses.
    """

    def __init__(
        self,
        base_url: str,
        problem_uid: str,
        api_key: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.problem_uid = problem_uid
        self.session = Session()
        if api_key:
            # automatically include API key on all requests
            self.session.headers.update({"api-key": api_key})

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        files: Any = None,
    ) -> dict[str, Any] | str:
        """
        Internal helper to perform an HTTP request and log details.
        """
        url = f"{self.base_url}/{self.problem_uid}{path}"
        logger.info("--> %s %s", method, url)
        if params:
            logger.info("    params=%s", params)
        if json is not None:
            logger.info("    json_payload=%s", json)
        if files:
            logger.info("    files=%s", files)

        response = self.session.request(
            method,
            url,
            params=params,
            json=json,
            files=files,
        )

        logger.info("<-- [%d] %s", response.status_code, response.url)
        text = response.text
        if len(text) > 500:
            logger.info("    response_text=%s... [truncated]", text[:500])
        else:
            logger.info("    response_text=%s", text)

        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return text

    def get_instance_schema(self) -> dict[str, Any]:
        """Returns the schema for problem instances."""
        return self._request("GET", "/instance_schema")  # type: ignore

    def get_instance(self, instance_uid: str) -> dict[str, Any]:
        """Fetches a specific problem instance by its UID."""
        return self._request("GET", f"/instances/{instance_uid}")  # type: ignore

    def get_all_instance_info(
        self,
        offset: int = 0,
        limit: int = 100,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Fetches all problem instances."""
        merged: dict[str, Any] = {"offset": offset, "limit": limit}
        if params:
            merged |= params
        return self._request("GET", "/instance_info", params=merged)  # type: ignore

    def get_instance_info(self, instance_uid: str) -> dict[str, Any]:
        """Fetches information about a specific problem instance."""
        return self._request("GET", f"/instance_info/{instance_uid}")  # type: ignore

    def get_problem_info(self) -> dict[str, Any]:
        """Fetches information about the problem."""
        return self._request("GET", "/problem_info/")  # type: ignore

    def upload_instance(self, instance: BaseModel) -> dict[str, Any]:
        """Uploads a new problem instance."""
        payload = instance.model_dump(mode="json")
        return self._request("POST", "/instances", json=payload)  # type: ignore

    def delete_instance(self, instance_uid: str) -> dict[str, Any]:
        """Deletes a problem instance by its UID."""
        return self._request("DELETE", f"/instances/{instance_uid}")  # type: ignore

    # Assets
    def get_assets(self, instance_uid: str) -> dict[str, Any]:
        """Fetches all assets for a problem instance."""
        return self._request("GET", f"/assets/{instance_uid}")  # type: ignore

    def upload_asset(
        self,
        instance_uid: str,
        asset_class: str,
        asset_path: str,
    ) -> dict[str, Any]:
        """Uploads an asset for a problem instance."""
        with open(asset_path, "rb") as f:
            files_data = {"file": f}
            return self._request(
                "POST", f"/assets/{asset_class}/{instance_uid}", files=files_data
            )  # type: ignore

    def delete_asset(self, instance_uid: str, asset_class: str) -> dict[str, Any]:
        """Deletes a specific asset for a problem instance."""
        return self._request("DELETE", f"/assets/{asset_class}/{instance_uid}")  # type: ignore

    # Solutions
    def get_solution_schema(self) -> dict[str, Any]:
        """Returns the schema for problem solutions."""
        return self._request("GET", "/solution_schema")  # type: ignore

    def get_solution_info(
        self,
        instance_uid: str,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Fetches the solutions for a specific problem instance."""
        params = {"offset": offset, "limit": limit}
        return self._request("GET", f"/solution_info/{instance_uid}", params=params)  # type: ignore

    def upload_solution(self, solution: BaseModel) -> dict[str, Any]:
        """Uploads a new solution for a problem instance."""
        payload = solution.model_dump(mode="json")
        return self._request("POST", "/solutions", json=payload)  # type: ignore

    def get_solution(self, solution_uid: str) -> dict[str, Any]:
        """Fetches a specific solution by its UID."""
        return self._request("GET", f"/solutions/{solution_uid}")  # type: ignore

    def delete_solution(self, solution_uid: str) -> dict[str, Any]:
        """Deletes a specific solution for a problem instance."""
        return self._request("DELETE", f"/solutions/{solution_uid}")  # type: ignore


