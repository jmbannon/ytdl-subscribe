from pathlib import Path
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional

from ytdl_sub.config.preset_options import Overrides
from ytdl_sub.downloaders.downloader import DownloaderOptionsT
from ytdl_sub.downloaders.youtube.abc import YoutubeDownloader
from ytdl_sub.downloaders.youtube.abc import YoutubeDownloaderOptions
from ytdl_sub.entries.youtube import YoutubeChannel
from ytdl_sub.entries.youtube import YoutubeVideo
from ytdl_sub.utils.logger import Logger
from ytdl_sub.utils.thumbnail import convert_url_thumbnail
from ytdl_sub.validators.date_range_validator import DateRangeValidator
from ytdl_sub.validators.string_formatter_validators import OverridesStringFormatterValidator
from ytdl_sub.validators.url_validator import YoutubeChannelUrlValidator
from ytdl_sub.validators.validators import BoolValidator
from ytdl_sub.ytdl_additions.enhanced_download_archive import EnhancedDownloadArchive

logger = Logger.get()


class YoutubeChannelDownloaderOptions(YoutubeDownloaderOptions, DateRangeValidator):
    """
    Downloads all videos from a youtube channel.

    Usage:

    .. code-block:: yaml

      presets:
        my_example_preset:
          youtube:
            # required
            download_strategy: "channel"
            channel_url: "UCsvn_Po0SmunchJYtttWpOxMg"
            # optional
            channel_avatar_path: "poster.jpg"
            channel_banner_path: "fanart.jpg"
            download_individually: True
            before: "now"
            after: "today-2weeks"
    """

    _required_keys = {"channel_url"}
    _optional_keys = {
        "before",
        "after",
        "channel_avatar_path",
        "channel_banner_path",
        "download_individually",
    }

    def __init__(self, name, value):
        YoutubeDownloaderOptions.__init__(self, name, value)
        DateRangeValidator.__init__(self, name, value)
        self._channel_url = self._validate_key(
            "channel_url", YoutubeChannelUrlValidator
        ).channel_url
        self._channel_avatar_path = self._validate_key_if_present(
            "channel_avatar_path", OverridesStringFormatterValidator
        )
        self._channel_banner_path = self._validate_key_if_present(
            "channel_banner_path", OverridesStringFormatterValidator
        )
        self._download_individually = self._validate_key_if_present(
            "download_individually", BoolValidator, default=True
        )

    @property
    def channel_url(self) -> str:
        """
        Required. The channel's url, i.e.
        ``https://www.youtube.com/channel/UCsvn_Po0SmunchJYOWpOxMg``. URLs with ``/username`` or
        ``/c`` are valid to use.
        """
        return self._channel_url

    @property
    def channel_avatar_path(self) -> Optional[OverridesStringFormatterValidator]:
        """
        Optional. Path to store the channel's avatar thumbnail image to.
        """
        return self._channel_avatar_path

    @property
    def channel_banner_path(self) -> Optional[OverridesStringFormatterValidator]:
        """
        Optional. Path to store the channel's banner image to.
        """
        return self._channel_banner_path

    @property
    def download_individually(self) -> Optional[bool]:
        """
        Optional. Downloads files from the channel individually instead of in bulk. Setting to True
        is safer when downloading large amounts of videos in case an error occurs. Downloading by
        bulk (by setting to False) can increase speeds. Defaults to True.
        """
        return self._download_individually.value


class YoutubeChannelDownloader(YoutubeDownloader[YoutubeChannelDownloaderOptions, YoutubeVideo]):
    downloader_options_type = YoutubeChannelDownloaderOptions
    downloader_entry_type = YoutubeVideo

    # pylint: disable=line-too-long
    @classmethod
    def ytdl_option_defaults(cls) -> Dict:
        """
        Default `ytdl_options`_ for ``channel``

        .. code-block:: yaml

           ytdl_options:
             ignoreerrors: True  # ignore errors like hidden videos, age restriction, etc
             break_on_existing: True  # stop downloads (newest to oldest) if a video is already downloaded
             break_on_reject: True  # stops downloads if the video's upload date is out of the specified 'before'/'after' range
        """
        return dict(
            super().ytdl_option_defaults(),
            **{
                "break_on_existing": True,
                "break_on_reject": True,
            },
        )

    # pylint: enable=line-too-long

    def __init__(
        self,
        download_options: DownloaderOptionsT,
        enhanced_download_archive: EnhancedDownloadArchive,
        ytdl_options: Optional[Dict] = None,
    ):
        super().__init__(
            download_options=download_options,
            enhanced_download_archive=enhanced_download_archive,
            ytdl_options=ytdl_options,
        )
        self.channel: Optional[YoutubeChannel] = None

    def _get_channel_from_entry_dicts(self, entry_dicts: List[Dict]) -> YoutubeChannel:
        channel_entry_dict = [
            entry_dict for entry_dict in entry_dicts if entry_dict.get("extractor") == "youtube:tab"
        ][0]
        return YoutubeChannel(
            entry_dict=channel_entry_dict, working_directory=self.working_directory
        )

    def download(self) -> Generator[YoutubeVideo, None, None]:
        """
        Downloads all videos from a channel
        """
        ytdl_options_overrides = {}

        # If downloading individually, dry-run the entire channel download first, this will get the
        # videos that will be downloaded. Afterwards, download each video one-by-one
        if self.download_options.download_individually:
            ytdl_options_overrides["skip_download"] = True
            ytdl_options_overrides["writethumbnail"] = False

        # If a date range is specified when download a YT channel, add it into the ytdl options
        source_date_range = self.download_options.get_date_range()
        if source_date_range:
            ytdl_options_overrides["daterange"] = source_date_range

        entry_dicts = self.extract_info_via_info_json(
            ytdl_options_overrides=ytdl_options_overrides, url=self.download_options.channel_url
        )
        self.channel = self._get_channel_from_entry_dicts(entry_dicts=entry_dicts)

        # If downloading individually, remove the skip_download to actually download the video
        if self.download_options.download_individually:
            del ytdl_options_overrides["skip_download"]
            del ytdl_options_overrides["writethumbnail"]

        for entry_dict in entry_dicts:
            if entry_dict.get("extractor") == "youtube":
                # Only do the individual download if it is not dry-run and downloading individually
                if not self.is_dry_run and self.download_options.download_individually:
                    ytdl_options_overrides["playlist_items"] = str(entry_dict.get("playlist_index"))
                    _ = self.extract_info(
                        ytdl_options_overrides=ytdl_options_overrides,
                        url=self.download_options.channel_url,
                    )
                yield YoutubeVideo(entry_dict=entry_dict, working_directory=self.working_directory)

    def _download_thumbnail(
        self,
        thumbnail_url: str,
        output_thumbnail_path: str,
    ):
        """
        Downloads a thumbnail and stores it in the output directory

        Parameters
        ----------
        thumbnail_url:
            Url of the thumbnail
        output_thumbnail_path:
            Path to store the thumbnail after downloading
        """
        if not thumbnail_url:
            logger.warning("Could not find a thumbnail for %s", self.channel.uid)
            return

        convert_url_thumbnail(
            thumbnail_url=thumbnail_url, output_thumbnail_path=output_thumbnail_path
        )

    def post_download(self, overrides: Overrides):
        """
        Downloads and moves channel avatar and banner images to the output directory.

        Parameters
        ----------
        overrides
            Overrides that can contain variables in the avatar or banner file path
        """
        avatar_thumbnail_name = overrides.apply_formatter(self.download_options.channel_avatar_path)
        self._download_thumbnail(
            thumbnail_url=self.channel.avatar_thumbnail_url(),
            output_thumbnail_path=str(Path(self.working_directory) / avatar_thumbnail_name),
        )
        self.save_file(file_name=avatar_thumbnail_name)

        banner_thumbnail_name = overrides.apply_formatter(self.download_options.channel_banner_path)
        self._download_thumbnail(
            thumbnail_url=self.channel.banner_thumbnail_url(),
            output_thumbnail_path=str(Path(self.working_directory) / banner_thumbnail_name),
        )
        self.save_file(file_name=banner_thumbnail_name)
