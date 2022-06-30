import os
from pathlib import Path
from shutil import copyfile
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Union


class FileMetadata:
    def __init__(self, metadata: Optional[List[str]] = None):
        self.metadata: List[str] = metadata if metadata else []

    def append(self, other: "FileMetadata") -> "FileMetadata":
        self.metadata.extend(other.metadata)
        return self


class FileHandlerTransactionLog:
    """
    Tracks file 'transactions' performed by a FileHandler
    """

    def __init__(self):
        self.files_created: Dict[str, FileMetadata] = {}
        self.files_removed: Set[str] = set()

    def log_created_file(
        self, file_name: str, file_metadata: Optional[FileMetadata] = None
    ) -> "FileHandlerTransactionLog":
        if not file_metadata:
            file_metadata = FileMetadata()

        if file_name in self.files_created:
            raise ValueError(
                "Adding a file to the file handler transaction log that already exists"
            )

        self.files_created[file_name] = file_metadata
        return self

    def log_removed_file(self, file_name: str) -> "FileHandlerTransactionLog":
        self.files_removed.add(file_name)
        return self


class FileHandler:
    """
    Performs and tracks all file moving/copying/deleting
    """

    def __init__(self, working_directory: str, output_directory: str, dry_run: bool):
        self.dry_run = dry_run
        self.working_directory = working_directory
        self.output_directory = output_directory
        self._file_handler_transaction_log = FileHandlerTransactionLog()

    @classmethod
    def copy(cls, src_file_path: Union[str, Path], dst_file_path: Union[str, Path]):
        copyfile(src=src_file_path, dst=dst_file_path)

    @classmethod
    def delete(cls, file_path: Union[str, Path]):
        if os.path.isfile(file_path):
            os.remove(file_path)

    def copy_file_to_output_directory(self, file_name: str, output_file_name: str):
        self._file_handler_transaction_log.log_created_file(output_file_name)

        if not self.dry_run:
            output_file_path = Path(self.output_directory) / output_file_name
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            self.copy(
                src_file_path=Path(self.working_directory) / file_name,
                dst_file_path=output_file_path,
            )

    def delete_file_from_output_directory(self, file_name: str):
        file_path = Path(self.output_directory) / file_name
        exists = os.path.isfile(file_path)

        if exists:
            self._file_handler_transaction_log.log_removed_file(file_name)
            if not self.dry_run:
                self.delete(file_path=file_path)
