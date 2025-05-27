from pathlib import Path

from .safe_file_operations import SafeFileOperations
from .instance_repository import check_uid_pattern
from .problem_info import ProblemInfo


class AssetRepository:
    def __init__(self, problem_info: ProblemInfo):
        self.problem_info = problem_info
        self.root = problem_info.assets_root
        self._safe_file_ops = SafeFileOperations(self.root)

    def add(self, asset_class, instance_uid, asset, exists_ok: bool = False) -> Path:
        """
        Add a binary asset to the repository.
        """
        check_uid_pattern(instance_uid)
        extension = self.problem_info.assets[asset_class]
        asset_path = self.root / asset_class / f"{instance_uid}.{extension}"
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        if asset_path.exists() and not exists_ok:
            raise ValueError(f"An asset with the uid {instance_uid} already exists")
        with open(asset_path, "wb") as file:
            file.write(asset)
        return asset_path

    def delete_assets(self, instance_uid: str, asset_class: str | None = None):
        """
        Delete the assets with the given instance_uid.
        """
        check_uid_pattern(instance_uid)
        asset_dir = self.root
        if not self._safe_file_ops.exists(asset_dir):
            return
        if asset_class is not None:
            asset_path = (
                asset_dir
                / asset_class
                / f"{instance_uid}.{self.problem_info.assets[asset_class]}"
            )
            self._safe_file_ops.delete(asset_path)
        else:
            for asset_class, extension in self.problem_info.assets.items():
                asset_path = asset_dir / asset_class / f"{instance_uid}.{extension}"
                self._safe_file_ops.delete(asset_path)

    def available_assets_for_instance(self, instance_uid: str) -> dict[str, Path]:
        """
        Get the available assets for the instance with the given instance_uid.
        """
        check_uid_pattern(instance_uid)
        asset_dir = self.root
        if not self._safe_file_ops.exists(asset_dir):
            return {}
        assets = {}
        for asset_class, extension in self.problem_info.assets.items():
            asset_path = asset_dir / asset_class / f"{instance_uid}.{extension}"
            if self._safe_file_ops.exists(asset_path):
                assets[asset_class] = asset_path.relative_to(self.root)
        return assets

    def get_url(self, instance_uid: str, asset_class: str) -> str:
        """
        Get the URL for the asset with the given instance_uid and asset_class.
        """
        check_uid_pattern(instance_uid)
        extension = self.problem_info.assets[asset_class]
        return f"{self.problem_info.assets_url_root}/{asset_class}/{instance_uid}.{extension}"
