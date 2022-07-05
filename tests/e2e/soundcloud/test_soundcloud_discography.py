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
    return "examples/soundcloud_discography_config.yaml"


@pytest.fixture
def subscription_name():
    return "jb"


@pytest.fixture
def config(config_path):
    return ConfigFile.from_file_path(config_path=config_path)


@pytest.fixture
def subscription_dict(output_directory, subscription_name):
    return {
        "preset": "sc_discography",
        "soundcloud": {"url": "https://soundcloud.com/jessebannon"},
        # override the output directory with our fixture-generated dir
        "output_options": {"output_directory": output_directory},
        # download the worst format so it is fast
        "ytdl_options": {
            "format": "worst[ext=mp3]",
        },
        "overrides": {"artist": "j_b"},
    }


@pytest.fixture
def discography_subscription(config, subscription_name, subscription_dict):
    discography_preset = Preset.from_dict(
        config=config,
        preset_name=subscription_name,
        preset_dict=subscription_dict,
    )

    return Subscription.from_preset(
        preset=discography_preset,
        config=config,
    )


@pytest.fixture
def expected_discography_download():
    # turn off black formatter here for readability
    # fmt: off
    return ExpectedDownloads(
        expected_downloads=[
            # Download mapping
            ExpectedDownloadFile(path=Path(".ytdl-sub-jb-download-archive.json"), md5="1a99156e9ece62539fb2608416a07200"),

            # Entry files (singles)
            ExpectedDownloadFile(path=Path("j_b/[2021] Baby Santana's Dorian Groove/01 - Baby Santana's Dorian Groove.mp3"), md5="bffbd558e12c6a9e029dc136a88342c4"),
            ExpectedDownloadFile(path=Path("j_b/[2021] Baby Santana's Dorian Groove/folder.jpg"), md5="967892be44b8c47e1be73f055a7c6f08"),

            ExpectedDownloadFile(path=Path("j_b/[2021] Purple Clouds/01 - Purple Clouds.mp3"), md5="038db58aebe2ba875b733932b42a94d6"),
            ExpectedDownloadFile(path=Path("j_b/[2021] Purple Clouds/folder.jpg"), md5="967892be44b8c47e1be73f055a7c6f08"),

            # Entry files (albums)
            ExpectedDownloadFile(path=Path("j_b/[2022] Acoustic Treats/01 - 20160426 184214.mp3"), md5="e145f0a2f6012768280c38655ca58065"),
            ExpectedDownloadFile(path=Path("j_b/[2022] Acoustic Treats/02 - 20160502 123150.mp3"), md5="60c8b8817a197a13e4bb90903af612c5"),
            ExpectedDownloadFile(path=Path("j_b/[2022] Acoustic Treats/03 - 20160504 143832.mp3"), md5="8265b7e4f79878af877bc6ecd9757efe"),
            ExpectedDownloadFile(path=Path("j_b/[2022] Acoustic Treats/04 - 20160601 221234.mp3"), md5="accf46b76891d2954b893d0f91d82816"),
            ExpectedDownloadFile(path=Path("j_b/[2022] Acoustic Treats/05 - 20160601 222440.mp3"), md5="e1f584f523336160d5c1104a61de77f3"),
            ExpectedDownloadFile(path=Path("j_b/[2022] Acoustic Treats/06 - 20170604 190236.mp3"), md5="f6885b25901177f0357649afe97328cc"),
            ExpectedDownloadFile(path=Path("j_b/[2022] Acoustic Treats/07 - 20170612 193646.mp3"), md5="fa057f221cbe4cf2442cd2fdb960743e"),
            ExpectedDownloadFile(path=Path("j_b/[2022] Acoustic Treats/08 - 20170628 215206.mp3"), md5="7794ae812c64580e2ac8fc457d5cc85f"),
            ExpectedDownloadFile(path=Path("j_b/[2022] Acoustic Treats/09 - Finding Home.mp3"), md5="adbf02eddb2090c008eb497d13ff84b9"),
            ExpectedDownloadFile(path=Path("j_b/[2022] Acoustic Treats/10 - Shallow Water WIP.mp3"), md5="65bb10c84366c71498161734f953e93d"),
            ExpectedDownloadFile(path=Path("j_b/[2022] Acoustic Treats/11 - Untold History.mp3"), md5="6904b2918e5dc38d9a9f72d967eb74bf"),
            ExpectedDownloadFile(path=Path("j_b/[2022] Acoustic Treats/folder.jpg"), md5="967892be44b8c47e1be73f055a7c6f08"),
        ]
    )
    # fmt: on


class TestSoundcloudDiscography:
    """
    Downloads my (bad) SC recordings I made. Ensure the above files exist and have the
    expected md5 file hashes.
    """

    @pytest.mark.parametrize("dry_run", [True, False])
    def test_discography_download(
        self, discography_subscription, expected_discography_download, output_directory, dry_run
    ):
        transaction_log = discography_subscription.download(dry_run=dry_run)
        assert_transaction_log_matches(
            output_directory=output_directory,
            transaction_log=transaction_log,
            transaction_log_summary_file_name="soundcloud/test_soundcloud_discography.txt",
        )
        if not dry_run:
            expected_discography_download.assert_files_exist(relative_directory=output_directory)
