import contextlib
import copy
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

import yt_dlp as ytdl
from yt_dlp.utils import ExistingVideoReached
from yt_dlp.utils import MaxDownloadsReached
from yt_dlp.utils import RejectedVideoReached

from ytdl_sub.thread.log_entries_downloaded_listener import LogEntriesDownloadedListener
from ytdl_sub.utils.exceptions import FileNotDownloadedException
from ytdl_sub.utils.logger import Logger


class YTDLP:
    _EXTRACT_ENTRY_NUM_RETRIES: int = 5
    _EXTRACT_ENTRY_RETRY_WAIT_SEC: int = 5

    logger = Logger.get(name="yt-dlp-downloader")

    @classmethod
    @contextmanager
    def ytdlp_downloader(cls, ytdl_options_overrides: Dict) -> ytdl.YoutubeDL:
        """
        Context manager to interact with yt_dlp.
        """
        cls.logger.debug("ytdl_options: %s", str(ytdl_options_overrides))
        with Logger.handle_external_logs(name="yt-dlp"):
            # Deep copy ytdl_options in case yt-dlp modifies the dict
            with ytdl.YoutubeDL(copy.deepcopy(ytdl_options_overrides)) as ytdl_downloader:
                yield ytdl_downloader

    @classmethod
    def extract_info(cls, ytdl_options_overrides: Dict, **kwargs) -> Dict:
        """
        Wrapper around yt_dlp.YoutubeDL.YoutubeDL.extract_info
        All kwargs will passed to the extract_info function.

        Parameters
        ----------
        ytdl_options_overrides
            Optional. Dict containing ytdl args to override other predefined ytdl args
        **kwargs
            arguments passed directory to YoutubeDL extract_info
        """
        with cls.ytdlp_downloader(ytdl_options_overrides) as ytdlp:
            return ytdlp.extract_info(**kwargs)

    @classmethod
    def extract_info_with_retry(
        cls,
        ytdl_options_overrides: Dict,
        is_downloaded_fn: Optional[Callable[[], bool]] = None,
        is_thumbnail_downloaded_fn: Optional[Callable[[], bool]] = None,
        **kwargs,
    ) -> Dict:
        """
        Wrapper around yt_dlp.YoutubeDL.YoutubeDL.extract_info
        All kwargs will passed to the extract_info function.

        This should be used when downloading a single entry. Checks if the entry's video
        and thumbnail files exist - retry if they do not.

        Parameters
        ----------
        ytdl_options_overrides
            Dict containing ytdl args to override other predefined ytdl args
        is_downloaded_fn
            Optional. Function to check if the entry is downloaded
        is_thumbnail_downloaded_fn
            Optional. Function to check if the entry thumbnail is downloaded
        **kwargs
            arguments passed directory to YoutubeDL extract_info

        Raises
        ------
        FileNotDownloadedException
            If the entry fails to download
        """
        num_tries = 0
        copied_ytdl_options_overrides = copy.deepcopy(ytdl_options_overrides)

        is_downloaded = False
        entry_dict: Optional[Dict] = None

        while num_tries < cls._EXTRACT_ENTRY_NUM_RETRIES:
            entry_dict = cls.extract_info(
                ytdl_options_overrides=copied_ytdl_options_overrides, **kwargs
            )

            is_downloaded = is_downloaded_fn is None or is_downloaded_fn()
            is_thumbnail_downloaded = (
                is_thumbnail_downloaded_fn is None or is_thumbnail_downloaded_fn()
            )

            if is_downloaded and is_thumbnail_downloaded:
                return entry_dict or {}  # in-case yt-dlp returns None

            # Always add check_formats
            # See https://github.com/yt-dlp/yt-dlp/issues/502
            copied_ytdl_options_overrides["check_formats"] = True

            # If the video file is downloaded but the thumbnail is not, then do not download
            # the video again
            if is_downloaded and not is_thumbnail_downloaded:
                copied_ytdl_options_overrides["skip_download"] = True
                copied_ytdl_options_overrides["writethumbnail"] = True

            time.sleep(cls._EXTRACT_ENTRY_RETRY_WAIT_SEC)
            num_tries += 1

            # Remove the download archive to retry without thinking its already downloaded,
            # even though it is not
            if "download_archive" in copied_ytdl_options_overrides:
                del copied_ytdl_options_overrides["download_archive"]

            if num_tries < cls._EXTRACT_ENTRY_NUM_RETRIES:
                cls.logger.info(
                    "Failed to download entry. Retrying %d / %d",
                    num_tries,
                    cls._EXTRACT_ENTRY_NUM_RETRIES,
                )

        # Still return if the media file downloaded (thumbnail could be missing)
        if is_downloaded and entry_dict is not None:
            return entry_dict

        error_dict = {"ytdl_options": ytdl_options_overrides, "kwargs": kwargs}
        raise FileNotDownloadedException(
            f"yt-dlp failed to download an entry with these arguments: {error_dict}"
        )

    @classmethod
    def _get_entry_dicts_from_info_json_files(cls, working_directory: str) -> List[Dict]:
        """
        Parameters
        ----------
        working_directory
            Directory that info json files are located

        Returns
        -------
        List of all info.json files read as JSON dicts
        """
        entry_dicts: List[Dict] = []
        info_json_paths = [
            Path(working_directory) / file_name
            for file_name in os.listdir(working_directory)
            if file_name.endswith(".info.json")
        ]

        for info_json_path in info_json_paths:
            with open(info_json_path, "r", encoding="utf-8") as file:
                entry_dicts.append(json.load(file))

        return entry_dicts

    @classmethod
    @contextlib.contextmanager
    def _listen_and_log_downloaded_info_json(
        cls, working_directory: str, log_prefix: Optional[str]
    ):
        """
        Context manager that starts a separate thread that listens for new .info.json files,
        prints their titles as they appear
        """
        if not log_prefix:
            yield
            return

        info_json_listener = LogEntriesDownloadedListener(
            working_directory=working_directory,
            log_prefix=log_prefix,
        )

        info_json_listener.start()

        try:
            yield
        finally:
            info_json_listener.complete = True

    @classmethod
    def extract_info_via_info_json(
        cls,
        working_directory: str,
        ytdl_options_overrides: Dict,
        log_prefix_on_info_json_dl: Optional[str] = None,
        **kwargs,
    ) -> List[Dict]:
        """
        Wrapper around yt_dlp.YoutubeDL.YoutubeDL.extract_info with infojson enabled. Entry dicts
        are extracted via reading all info.json files in the working directory rather than
        from the output of extract_info.

        This allows us to catch RejectedVideoReached and ExistingVideoReached exceptions, and
        simply ignore while still being able to read downloaded entry metadata.

        Parameters
        ----------
        working_directory
            Directory that info json files reside in
        ytdl_options_overrides
            Dict containing ytdl args to override other predefined ytdl args
        log_prefix_on_info_json_dl
            Optional. Spin a new thread to listen for new info.json files. Log
            f'{log_prefix_on_info_json_dl} {title}' when a new one appears
        **kwargs
            arguments passed directory to YoutubeDL extract_info
        """
        try:
            with cls._listen_and_log_downloaded_info_json(
                working_directory=working_directory, log_prefix=log_prefix_on_info_json_dl
            ):
                cls.extract_info(ytdl_options_overrides=ytdl_options_overrides, **kwargs)
        except RejectedVideoReached:
            cls.logger.info(
                "RejectedVideoReached, stopping additional downloads "
                "(Can be disable by setting `date_range.breaks` to False. "
                "If this is unexpected, "
                "run with `--log-level verbose` to see the yt-dlp logs on why it stopped)"
            )
        except ExistingVideoReached:
            cls.logger.info(
                "ExistingVideoReached, stopping additional downloads. "
                "(Can be disable by setting `ytdl_options.break_on_existing` to False. This will "
                "force yt-dlp to continue scraping all metadata to grab any files you may have "
                "missed)"
            )
        except MaxDownloadsReached:
            cls.logger.info("MaxDownloadsReached, stopping additional downloads.")

        parent_dicts: List[Dict] = []
        entry_dicts = cls._get_entry_dicts_from_info_json_files(working_directory=working_directory)
        entry_ids = {entry_dict.get("id") for entry_dict in entry_dicts}

        # Try to get additional uploader (source) metadata that yt-dlp does not fetch
        # in a single request
        for entry_dict in entry_dicts:
            if not (uploader_id := entry_dict.get("uploader_id")):
                continue

            if uploader_id in entry_ids or not (uploader_url := entry_dict.get("uploader_url")):
                continue

            cls.logger.info("Attempting to get parent metadata from URL %s", uploader_url)
            parent_dict: Optional[Dict] = None
            try:
                parent_dict = cls.extract_info(
                    ytdl_options_overrides=ytdl_options_overrides | {"playlist_items": "0:0"},
                    url=uploader_url,
                )
            except Exception:  # pylint: disable=broad-except
                pass

            parent_id = parent_dict.get("id") if isinstance(parent_dict, dict) else None
            if parent_id and parent_id not in entry_ids:
                parent_dicts.append(parent_dict)
                entry_ids.add(parent_id)
                cls.logger.debug("Adding parent metadata with ids [%s, %s]", uploader_id, parent_id)

            # Always add the uploader_id since it has been tried
            entry_ids.add(uploader_id)

        return entry_dicts + parent_dicts
