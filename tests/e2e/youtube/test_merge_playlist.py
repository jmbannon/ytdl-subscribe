from pathlib import Path

import pytest
from e2e.expected_download import ExpectedDownloadFile
from e2e.expected_download import ExpectedDownloads
from e2e.expected_transaction_log import assert_transaction_log_matches

from ytdl_sub.config.config_file import ConfigFile
from ytdl_sub.config.preset import Preset
from ytdl_sub.subscriptions.subscription import Subscription


@pytest.fixture
def config_path():
    return "examples/kodi_music_videos_config.yaml"


@pytest.fixture
def subscription_name():
    return "jmc"


@pytest.fixture
def config(config_path):
    return ConfigFile.from_file_path(config_path=config_path)


@pytest.fixture
def subscription_dict(output_directory, subscription_name):
    return {
        "preset": "yt_music_video_playlist",
        "youtube": {
            "download_strategy": "merge_playlist",
            "playlist_url": "https://youtube.com/playlist?list=PL5BC0FC26BECA5A35",
            "add_chapters": True,
        },
        # override the output directory with our fixture-generated dir
        "output_options": {"output_directory": output_directory},
        # download the worst format so it is fast
        "ytdl_options": {
            "format": "best[height<=480]",
            "postprocessor_args": {"ffmpeg": ["-bitexact"]},  # Must add this for reproducibility
        },
        "overrides": {"artist": "JMC"},
    }


####################################################################################################
# PLAYLIST FIXTURES


@pytest.fixture
def playlist_subscription(config, subscription_name, subscription_dict):
    playlist_preset = Preset.from_dict(
        config=config,
        preset_name=subscription_name,
        preset_dict=subscription_dict,
    )

    return Subscription.from_preset(
        preset=playlist_preset,
        config=config,
    )


@pytest.fixture
def expected_playlist_download():
    # fmt: off
    return ExpectedDownloads(
        expected_downloads=[
            ExpectedDownloadFile(path=Path("JMC - Jesse's Minecraft Server-thumb.jpg"), md5="a3f1910f9c51f6442f845a528e190829"),
            ExpectedDownloadFile(path=Path("JMC - Jesse's Minecraft Server.mkv"), md5=["6053c47a8690519b0a33c13fa4b01ac0", "3ab42b3e6be0a44deb3a9a28e6ebaf16"]),
            ExpectedDownloadFile(path=Path("JMC - Jesse's Minecraft Server.nfo"), md5="10df5dcdb65ab18ecf21b3503c77e48b"),
        ]
    )
    # fmt: on


class TestYoutubeMergePlaylist:
    """
    Downloads my old minecraft youtube channel, pretends they are music videos. Ensure the above
    files exist and have the expected md5 file hashes.
    """

    @pytest.mark.parametrize("dry_run", [True, False])
    def test_merge_playlist_download(
        self, playlist_subscription, expected_playlist_download, output_directory, dry_run
    ):
        transaction_log = playlist_subscription.download()
        assert_transaction_log_matches(
            output_directory=output_directory,
            transaction_log=transaction_log,
            transaction_log_summary_file_name="test_merge_playlist.txt",
        )

        if not dry_run:
            expected_playlist_download.assert_files_exist(relative_directory=output_directory)
