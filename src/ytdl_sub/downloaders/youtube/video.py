from typing import Dict
from typing import List

from ytdl_sub.downloaders.generic.collection import CollectionDownloader
from ytdl_sub.downloaders.generic.collection import CollectionDownloadOptions
from ytdl_sub.downloaders.youtube.abc import YoutubeDownloader
from ytdl_sub.downloaders.youtube.abc import YoutubeDownloaderOptions
from ytdl_sub.entries.youtube import YoutubeVideo
from ytdl_sub.validators.url_validator import YoutubeVideoUrlValidator


class YoutubeVideoDownloaderOptions(YoutubeDownloaderOptions):
    """
    Downloads a single youtube video. This download strategy is intended for CLI usage performing
    a one-time download of a video, not a subscription.

    Usage:

    .. code-block:: yaml

      presets:
        example_preset:
          youtube:
            # required
            download_strategy: "video"
            video_url: "youtube.com/watch?v=VMAPTo7RVDo"

    CLI usage:

    .. code-block:: bash

       ytdl-sub dl --preset "example_preset" --youtube.video_url "youtube.com/watch?v=VMAPTo7RVDo"
    """

    _required_keys = {"video_url"}

    def __init__(self, name, value):
        super().__init__(name, value)
        self._video_url = self._validate_key("video_url", YoutubeVideoUrlValidator).video_url

        self.collection_validator = CollectionDownloadOptions(
            name=self._name,
            value={"urls": [{"url": self.video_url}]},
        )

    @property
    def video_url(self) -> str:
        """
        Required. The url of the video, i.e. ``youtube.com/watch?v=VMAPTo7RVDo``.
        """
        return self._video_url


class YoutubeVideoDownloader(YoutubeDownloader[YoutubeVideoDownloaderOptions, YoutubeVideo]):
    downloader_options_type = YoutubeVideoDownloaderOptions
    downloader_entry_type = YoutubeVideo

    @classmethod
    def ytdl_option_defaults(cls) -> Dict:
        """
        Default `ytdl_options`_ for ``video``

        .. code-block:: yaml

           ytdl_options:
             ignoreerrors: True  # ignore errors like hidden videos, age restriction, etc
        """
        return dict(
            super().ytdl_option_defaults(),
            **{"break_on_existing": True},
        )

    def download(self) -> List[YoutubeVideo]:
        """Download a single Youtube video"""
        downloader = CollectionDownloader(
            download_options=self.download_options.collection_validator,
            enhanced_download_archive=self._enhanced_download_archive,
            ytdl_options_builder=self._ytdl_options_builder,
            overrides=self.overrides,
        )

        for entry in downloader.download():
            # pylint: disable=protected-access
            yield YoutubeVideo(entry_dict=entry._kwargs, working_directory=self.working_directory)
            # pylint: enable=protected-access
