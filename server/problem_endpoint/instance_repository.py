import logging
from pathlib import Path
from typing import Type, TypeVar, Generic
from pydantic import BaseModel
import lzma

from .problem_info import ProblemInfo

# Define a generic type variable for the instance model
T = TypeVar("T", bound=BaseModel)


def check_uid_pattern(instance_uid: str, fail: bool = True) -> bool:
    """
    Check if the instance_uid is valid. They are only allowed to contain alphanumeric characters, dashes, and underscores, and slashes for subdirectories. They are not allowed to start or end with a slash.
    """
    if (
        not all(c.isalnum() or c in "-_/" for c in instance_uid)
        or instance_uid.startswith("/")
        or instance_uid.endswith("/")
    ):
        if not fail:
            return False
        logging.error(
            "The instance_uid %s is not valid. It can only contain alphanumeric characters, dashes, and underscores, and slashes for subdirectories. It cannot start or end with a slash.",
            instance_uid,
        )
        raise ValueError(
            "The instance_uid can only contain alphanumeric characters, dashes, and underscores, and slashes for subdirectories."
        )
    return True


class LocalFileSystemWithCompression:
    """
    This class saves and loads pydantic models to and from the local file system with compression.
    """

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def exists(self, uid: str) -> bool:
        """
        Check if a file with the given uid exists.
        """
        path = (self.root / uid).with_suffix(".json.xz")
        return path.exists()

    def save(self, data: BaseModel, uid: str, exists_ok: bool = False) -> Path:
        """
        Save the data to the given path.
        """
        path = Path(uid)
        path = self.root / path.with_suffix(".json.xz")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not exists_ok:
            raise ValueError(f"The file {uid} already exists")
        with lzma.open(path, "wt") as file:
            file.write(data.model_dump_json())
        return path.relative_to(self.root)

    def load(self, model: Type[T], uid: str) -> T:
        """
        Load the data from the given path.
        """
        path = (self.root / uid).with_suffix(".json.xz")
        if not path.exists():
            logging.error(
                "LocalFileSystemWithCompression: No file found for %s under %s",
                uid,
                path,
            )
            raise KeyError(f"No file found for {uid}")
        with lzma.open(path, "rt") as file:
            return model.model_validate_json(file.read())

    def delete(self, uid: str):
        """
        Delete the file with the given uid.
        """
        path = (self.root / uid).with_suffix(".json.xz")
        if path.exists():
            path.unlink()

    def all_uids(self) -> list[str]:
        """
        Get all the uids in the root directory.
        """
        suffix = ".json.xz"
        uids = [
            str(p.relative_to(self.root))[: -len(suffix)]
            for p in self.root.glob(f"**/*{suffix}")
        ]
        uids = [uid for uid in uids if check_uid_pattern(uid, fail=False)]
        return uids

    def all_uids_beginning_with(self, prefix: str) -> list[str]:
        """
        Get all the uids that start with the given prefix.
        """
        suffix = ".json.xz"
        prefix = prefix.rstrip("/")
        uids = [
            str(p.relative_to(self.root))[: -len(suffix)]
            for p in self.root.glob(f"{prefix}/**/*{suffix}")
        ]
        uids = [uid for uid in uids if check_uid_pattern(uid, fail=False)]
        return uids


class InstanceRepository(Generic[T]):
    """
    This class manages the file based instance storage.
    Note that this may be replaced by a cloud storage or a database later.
    """

    def __init__(self, problem_info: ProblemInfo):
        self.problem_info = problem_info
        self.instance_model: Type[T] = problem_info.instance_model  # type: ignore
        self.file_system = LocalFileSystemWithCompression(problem_info.instances_root)

    def exists(self, instance_uid: str) -> bool:
        """
        Check if an instance with the given instance_uid exists.
        """
        check_uid_pattern(instance_uid)
        return self.file_system.exists(instance_uid)

    def read_instance(self, instance_uid: str) -> T:
        """
        Get the instance with the given instance_uid.
        It will be in problem_info.path/instances/instance_uid.json.xz
        Returns the instance as a Pydantic model.
        """
        check_uid_pattern(instance_uid)
        instance = self.file_system.load(self.instance_model, instance_uid)
        if getattr(instance, self.problem_info.uid_attribute) != instance_uid:
            logging.error(
                "The instance_uid of the instance %s does not match the file name %s",
                getattr(instance, self.problem_info.uid_attribute),
                instance_uid,
            )
            raise ValueError(
                f"The instance_uid of the instance {instance_uid} does not match the file name"
            )
        return instance

    def write_instance(self, instance: T, overwrite: bool = False):
        """
        Write the instance to the file system.
        """
        if not isinstance(instance, self.instance_model):
            logging.error(
                "The instance %s is not of the correct type %s",
                instance,
                self.instance_model,
            )
            raise ValueError("The instance is not of the correct type")
        instance_uid = getattr(instance, self.problem_info.uid_attribute)
        check_uid_pattern(instance_uid)
        self.file_system.save(instance, instance_uid, exists_ok=overwrite)

    def delete_instance(self, instance_uid: str):
        """
        Delete the instance with the given instance_uid.
        """
        check_uid_pattern(instance_uid)
        self.file_system.delete(instance_uid)

    def get_all_instance_uids(self) -> list[str]:
        """
        Get the unique identifiers of all instances.
        Iterate over the files in problem_info.path/instances and return the instance_uids.
        """
        return self.file_system.all_uids()

    def get_download_url(self, instance_uid: str) -> str:
        """
        Get the download URL of the instance with the given instance_uid.
        """
        check_uid_pattern(instance_uid)
        base_url = self.problem_info.instances_url_root.rstrip("/")
        return f"{base_url}/{instance_uid}.json.xz"
