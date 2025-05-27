from pathlib import Path
from .problem_info import ProblemInfo
from .instance_repository import LocalFileSystemWithCompression, check_uid_pattern
import hashlib


class SolutionRepository:
    def __init__(self, problem_info: ProblemInfo):
        self.problem_info = problem_info
        self.file_system = LocalFileSystemWithCompression(problem_info.solutions_root)
        if self.problem_info.solution_model is None:
            raise ValueError("The problem does not have a solution model")

    def exists(self, solution_uid: str) -> bool:
        """
        Check if a solution with the given solution_uid exists.
        """
        check_uid_pattern(solution_uid)
        return self.file_system.exists(solution_uid)

    def get_instance_uid_from_solution_uid(self, solution_uid: str) -> str:
        """
        Get the instance_uid from the solution_uid.
        """
        check_uid_pattern(solution_uid)
        # the instance uid is the part before the last slash
        return solution_uid.rsplit("/", 1)[0]

    def read_solution(self, solution_uid: str):
        """
        Get the solution with the given solution_uid.
        It will be in problem_info.path/solutions/solution_uid.json.xz
        Returns the solution as a Pydantic model.
        """
        check_uid_pattern(solution_uid)
        assert self.problem_info.solution_model is not None, (
            "The problem does not have a solution model"
        )
        solution = self.file_system.load(self.problem_info.solution_model, solution_uid)
        instance_uid = getattr(solution, self.problem_info.uid_attribute)
        if not solution_uid.startswith(instance_uid + "/"):
            raise ValueError(
                f"The instance uid of the solution {solution_uid} does not match the solution uid. Every solution uid should start with the instance uid."
            )
        return solution

    def write_solution(self, solution, overwrite: bool = True) -> tuple[str, Path]:
        """
        Write the solution to the file system.
        """
        assert self.problem_info.solution_model is not None, (
            "The problem does not have a solution model"
        )
        if not isinstance(solution, self.problem_info.solution_model):
            raise ValueError("The solution is not of the correct type")
        instance_uid = getattr(solution, self.problem_info.uid_attribute)
        solution_txt = solution.model_dump_json()
        # get a robust hash of the solution
        solution_hash = hashlib.md5(solution_txt.encode("utf-8")).hexdigest()
        solution_uid = f"{instance_uid}/{solution_hash}"
        check_uid_pattern(instance_uid)
        return solution_uid, self.file_system.save(
            solution, solution_uid, exists_ok=overwrite
        )

    def delete_solution(self, solution_uid: str):
        """
        Delete the solution with the given solution_uid.
        """
        check_uid_pattern(solution_uid)
        self.file_system.delete(solution_uid)

    def delete_all_solutions_of_instance(self, instance_uid: str):
        """
        Delete all the solutions of the instance with the given instance_uid.
        """
        check_uid_pattern(instance_uid)
        for solution_uid in self.list_solution_uids_of_instance(instance_uid):
            self.delete_solution(solution_uid)

    def list_solution_uids_of_instance(self, instance_uid: str) -> list[str]:
        """
        List the solution uids of the instance with the given instance_uid.
        """
        check_uid_pattern(instance_uid)
        uids = self.file_system.all_uids_beginning_with(instance_uid)
        return uids

    def list_all_solution_uids(self) -> list[str]:
        """
        List all the solution uids in the root directory.
        """
        return self.file_system.all_uids()
