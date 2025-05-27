from pathlib import Path
import lzma


class SafeFileOperations:
    def __init__(self, root: Path):
        self.root = root

    def open(self, path: Path | str, mode: str = "r"):
        """
        Open a file safely, ensuring the path is within the root directory.
        """
        if isinstance(path, str):
            path = Path(path)
        if not path.is_relative_to(self.root):
            raise ValueError(
                f"Path {path} is outside the allowed directory {self.root}"
            )
        return open(path, mode)

    def lzma_open(self, path: Path | str, mode: str = "rt"):
        """
        Open a file with lzma compression safely, ensuring the path is within the root directory.
        """
        if isinstance(path, str):
            path = Path(path)
        if not path.is_relative_to(self.root):
            raise ValueError(
                f"Path {path} is outside the allowed directory {self.root}"
            )
        return lzma.open(path, mode)

    def delete(self, path: Path | str):
        """
        Delete a file safely, ensuring the path is within the root directory.
        """
        if isinstance(path, str):
            path = Path(path)
        if not path.is_relative_to(self.root):
            raise ValueError(
                f"Path {path} is outside the allowed directory {self.root}"
            )
        path.unlink(missing_ok=True)

    def exists(self, path: Path | str) -> bool:
        """
        Check if a file exists safely, ensuring the path is within the root directory.
        """
        if isinstance(path, str):
            path = Path(path)
        if not path.is_relative_to(self.root):
            raise ValueError(
                f"Path {path} is outside the allowed directory {self.root}"
            )
        return path.exists()

    def execute(self, path, f):
        """
        Execute a function on a file safely, ensuring the path is within the root directory.
        """
        if isinstance(path, str):
            path = Path(path)
        if not path.is_relative_to(self.root):
            raise ValueError(
                f"Path {path} is outside the allowed directory {self.root}"
            )
        return f(path)
