import contextlib
import json
import os
import shutil
from abc import ABC
from pathlib import Path
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from ytdl_sub.entries.entry import Entry
from ytdl_sub.plugins.plugin import Plugin
from ytdl_sub.subscriptions.base_subscription import BaseSubscription
from ytdl_sub.subscriptions.subscription_ytdl_options import SubscriptionYTDLOptions
from ytdl_sub.utils.datetime import to_date_range
from ytdl_sub.utils.exceptions import ValidationException
from ytdl_sub.utils.file_handler import FileHandler
from ytdl_sub.utils.file_handler import FileHandlerTransactionLog
from ytdl_sub.utils.file_handler import FileMetadata
from ytdl_sub.utils.file_handler import get_file_extension
from ytdl_sub.utils.thumbnail import convert_download_thumbnail
from ytdl_sub.ytdl_additions.enhanced_download_archive import DownloadMappings


def _get_split_plugin(plugins: List[Plugin]) -> Optional[Plugin]:
    split_plugins = [plugin for plugin in plugins if plugin.is_split_plugin]

    if len(split_plugins) == 1:
        return split_plugins[0]
    if len(split_plugins) > 1:
        raise ValidationException("Can not use more than one split plugins at a time")
    return None


class SubscriptionDownload(BaseSubscription, ABC):
    """
    Handles the subscription download logic
    """

    def _move_entry_files_to_output_directory(
        self,
        dry_run: bool,
        entry: Entry,
        entry_metadata: Optional[FileMetadata] = None,
    ):
        """
        Helper function to move the media file and optionally thumbnail file to the output directory
        for a single entry.

        Parameters
        ----------
        dry_run
            Whether this session is a dry-run or not
        entry:
            The entry with files to move
        entry_metadata
            Optional. Metadata to record to the transaction log for this entry
        """
        # Move the file after all direct file modifications are complete
        output_file_name = self.overrides.apply_formatter(
            formatter=self.output_options.file_name, entry=entry
        )
        self._enhanced_download_archive.save_file_to_output_directory(
            file_name=entry.get_download_file_name(),
            file_metadata=entry_metadata,
            output_file_name=output_file_name,
            entry=entry,
        )

        # TODO: see if entry even has a thumbnail
        if self.output_options.thumbnail_name:
            output_thumbnail_name = self.overrides.apply_formatter(
                formatter=self.output_options.thumbnail_name, entry=entry
            )

            # We always convert entry thumbnails to jpgs, and is performed here
            if not dry_run:
                convert_download_thumbnail(entry=entry)

            # Copy the thumbnails since they could be used later for other things
            self._enhanced_download_archive.save_file_to_output_directory(
                file_name=entry.get_download_thumbnail_name(),
                output_file_name=output_thumbnail_name,
                entry=entry,
                copy_file=True,
            )

        if self.output_options.info_json_name:
            output_info_json_name = self.overrides.apply_formatter(
                formatter=self.output_options.info_json_name, entry=entry
            )

            # if not dry-run, write the info json
            if not dry_run:
                entry.write_info_json()

            self._enhanced_download_archive.save_file_to_output_directory(
                file_name=entry.get_download_info_json_name(),
                output_file_name=output_info_json_name,
                entry=entry,
            )

    def _delete_working_directory(self, is_error: bool = False) -> None:
        _ = is_error
        if os.path.isdir(self.working_directory):
            shutil.rmtree(self.working_directory)

    @contextlib.contextmanager
    def _prepare_working_directory(self):
        """
        Context manager to create all directories to the working directory. Deletes the entire
        working directory when cleaning up.
        """
        self._delete_working_directory()
        os.makedirs(self.working_directory, exist_ok=True)

        try:
            yield
        except Exception as exc:
            self._delete_working_directory(is_error=True)
            raise exc
        else:
            self._delete_working_directory()

    @contextlib.contextmanager
    def _maintain_archive_file(self):
        """
        Context manager to initialize the enhanced download archive
        """
        if self.maintain_download_archive:
            self._enhanced_download_archive.prepare_download_archive()

        yield

        # If output options maintains stale file deletion, perform the delete here prior to saving
        # the download archive
        if self.maintain_download_archive:
            date_range_to_keep = to_date_range(
                before=self.output_options.keep_files_before,
                after=self.output_options.keep_files_after,
                overrides=self.overrides,
            )
            if date_range_to_keep:
                self._enhanced_download_archive.remove_stale_files(date_range=date_range_to_keep)

            self._enhanced_download_archive.save_download_mappings()
            FileHandler.delete(self._enhanced_download_archive.archive_working_file_path)
            FileHandler.delete(self._enhanced_download_archive.mapping_working_file_path)

    @contextlib.contextmanager
    def _remove_empty_directories_in_output_directory(self):
        try:
            yield
        finally:
            if not self._enhanced_download_archive.is_dry_run:
                for root, dir_names, filenames in os.walk(Path(self.output_directory), topdown=False):
                    for dir_name in dir_names:
                        dir_path = Path(root) / dir_name
                        if len(os.listdir(dir_path)) == 0:
                            os.rmdir(dir_path)

    @contextlib.contextmanager
    def _subscription_download_context_managers(self) -> None:
        with (
            self._prepare_working_directory(),
            self._maintain_archive_file(),
            self._remove_empty_directories_in_output_directory(),
        ):
            yield

    def _initialize_plugins(self) -> List[Plugin]:
        """
        Returns
        -------
        List of plugins defined in the subscription, initialized and ready to use.
        """
        plugins: List[Plugin] = []
        for plugin_type, plugin_options in self.plugins.zipped():
            plugin = plugin_type(
                plugin_options=plugin_options,
                overrides=self.overrides,
                enhanced_download_archive=self._enhanced_download_archive,
            )

            plugins.append(plugin)

        return plugins

    @classmethod
    def _cleanup_entry_files(cls, entry: Entry):
        FileHandler.delete(entry.get_download_file_path())
        FileHandler.delete(entry.get_download_thumbnail_path())
        FileHandler.delete(entry.get_download_info_json_path())

    def _post_process_entry(
        self, plugins: List[Plugin], dry_run: bool, entry: Entry, entry_metadata: FileMetadata
    ):
        # Post-process the entry with all plugins
        for plugin in sorted(plugins, key=lambda _plugin: _plugin.priority.post_process):
            optional_plugin_entry_metadata = plugin.post_process_entry(entry)
            if optional_plugin_entry_metadata:
                entry_metadata.extend(optional_plugin_entry_metadata)

        # Then, move it to the output directory
        self._move_entry_files_to_output_directory(
            dry_run=dry_run, entry=entry, entry_metadata=entry_metadata
        )

        # Re-save the download archive after each entry is moved to the output directory
        if self.maintain_download_archive:
            self._enhanced_download_archive.save_download_mappings()

    def _process_entry(
        self, plugins: List[Plugin], dry_run: bool, entry: Entry, entry_metadata: FileMetadata
    ) -> None:
        entry_: Optional[Entry] = entry

        # First, modify the entry with all plugins
        for plugin in sorted(plugins, key=lambda _plugin: _plugin.priority.modify_entry):
            # Break if it is None, it is indicated to not process any further
            if (entry_ := plugin.modify_entry(entry_)) is None:
                break

        if entry_:
            self._post_process_entry(
                plugins=plugins, dry_run=dry_run, entry=entry_, entry_metadata=entry_metadata
            )

        self._cleanup_entry_files(entry)

    def _process_split_entry(
        self, split_plugin: Plugin, plugins: List[Plugin], dry_run: bool, entry: Entry
    ) -> None:
        entry_: Optional[Entry] = entry

        plugins_pre_split = sorted(
            [plugin for plugin in plugins if not plugin.priority.modify_entry_after_split],
            key=lambda _plugin: _plugin.priority.modify_entry,
        )

        plugins_post_split = sorted(
            [plugin for plugin in plugins if plugin.priority.modify_entry_after_split],
            key=lambda _plugin: _plugin.priority.modify_entry,
        )

        # First, modify the entry with pre_split plugins
        for plugin in plugins_pre_split:
            # Break if it is None, it is indicated to not process any further
            if (entry_ := plugin.modify_entry(entry_)) is None:
                break

        # Then, perform the split
        if entry_:
            for split_entry, split_entry_metadata in split_plugin.split(entry=entry_):
                split_entry_: Optional[Entry] = split_entry

                for plugin in plugins_post_split:
                    # Return if it is None, it is indicated to not process any further.
                    # Break out of the plugin loop
                    if (split_entry_ := plugin.modify_entry(split_entry_)) is None:
                        break

                # If split_entry is None from modify_entry, do not post process
                if split_entry_:
                    self._post_process_entry(
                        plugins=plugins,
                        dry_run=dry_run,
                        entry=split_entry_,
                        entry_metadata=split_entry_metadata,
                    )

                self._cleanup_entry_files(split_entry)

        self._cleanup_entry_files(entry)

    def _process_subscription(
        self,
        plugins: List[Plugin],
        entries: Iterable[Entry] | Iterable[Tuple[Entry, FileMetadata]],
        dry_run: bool,
    ) -> FileHandlerTransactionLog:
        for entry in entries:
            entry_metadata = FileMetadata()
            if isinstance(entry, tuple):
                entry, entry_metadata = entry

            if split_plugin := _get_split_plugin(plugins):
                self._process_split_entry(
                    split_plugin=split_plugin, plugins=plugins, dry_run=dry_run, entry=entry
                )
            else:
                self._process_entry(
                    plugins=plugins, dry_run=dry_run, entry=entry, entry_metadata=entry_metadata
                )

        for plugin in plugins:
            plugin.post_process_subscription()

        return self._enhanced_download_archive.get_file_handler_transaction_log()

    def download(self, dry_run: bool = False) -> FileHandlerTransactionLog:
        """
        Performs the subscription download

        Parameters
        ----------
        dry_run
            If true, do not download any video/audio files or move anything to the output
            directory.
        """
        self._enhanced_download_archive.reinitialize(dry_run=dry_run)
        plugins = self._initialize_plugins()

        subscription_ytdl_options = SubscriptionYTDLOptions(
            preset=self._preset_options,
            plugins=plugins,
            enhanced_download_archive=self._enhanced_download_archive,
            working_directory=self.working_directory,
            dry_run=dry_run,
        )

        with self._subscription_download_context_managers():
            downloader = self.downloader_class(
                download_options=self.downloader_options,
                enhanced_download_archive=self._enhanced_download_archive,
                download_ytdl_options=subscription_ytdl_options.download_builder(),
                metadata_ytdl_options=subscription_ytdl_options.metadata_builder(),
                overrides=self.overrides,
            )

            return self._process_subscription(
                plugins=plugins,
                entries=downloader.download(),
                dry_run=dry_run,
            )

    def _get_entries_for_reformat(
        self, download_mappings: DownloadMappings, dry_run: bool
    ) -> Iterable[Entry]:
        entry_mapping: List[Tuple[Entry, Set[str]]] = []
        for download_mapping in download_mappings._entry_mappings.values():
            maybe_entry: Optional[Entry] = None
            for file_name in download_mapping.file_names:
                if file_name.endswith(".info.json"):
                    try:
                        with open(
                            Path(self.output_directory) / file_name, "r", encoding="utf-8"
                        ) as maybe_info_json:
                            maybe_entry = Entry(
                                entry_dict=json.load(maybe_info_json),
                                working_directory=self.working_directory,
                            )
                    except Exception as exc:
                        raise ValidationException(
                            "info.json file cannot be loaded - subscription cannot be reformatted"
                        ) from exc

            if not maybe_entry:
                raise ValidationException(
                    ".info.json file could not be found - subscription cannot be reformatted"
                )

            entry_mapping.append((maybe_entry, download_mapping.file_names))

        for entry, file_names in entry_mapping:
            file_names_mtime: Dict[str, float] = {}
            for file_name in file_names:
                ext = get_file_extension(file_name)

                file_path = Path(self.output_directory) / file_name
                working_directory_file_path = Path(self.working_directory) / f"{entry.uid}.{ext}"

                file_names_mtime[file_name] = os.path.getmtime(file_path)

                # NFO files will always get rewritten, so ignore
                if ext == "nfo":
                    continue

                if not dry_run:
                    FileHandler.copy(
                        src_file_path=file_path,
                        dst_file_path=working_directory_file_path,
                    )

            yield entry

            for file_name, mtime in file_names_mtime.items():
                # If the entry file_path is unchanged, then delete it since it was not part of the
                # reformat output
                if os.path.getmtime(Path(self.output_directory) / file_name) == mtime:
                    self._enhanced_download_archive._file_handler.delete_file_from_output_directory(
                        file_name
                    )

    def update_with_info_json(self, dry_run: bool = False) -> FileHandlerTransactionLog:
        plugins = self._initialize_plugins()

        with self._subscription_download_context_managers():
            download_mappings = self._enhanced_download_archive.mapping
            self._enhanced_download_archive.reinitialize(dry_run=dry_run)

            return self._process_subscription(
                plugins=plugins,
                entries=self._get_entries_for_reformat(
                    download_mappings=download_mappings, dry_run=dry_run
                ),
                dry_run=dry_run,
            )
