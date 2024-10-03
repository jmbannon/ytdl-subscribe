from typing import Dict

import pytest

from ytdl_sub.entries.entry import ytdl_sub_chapters_from_comments
from ytdl_sub.subscriptions.subscription import Subscription


@pytest.fixture
def sponsorblock_disabled_dict(output_directory) -> Dict:
    return {
        "preset": "Jellyfin Music Videos",
        "output_options": {"output_directory": output_directory},
        "chapters": {
            "enable": "{enable_sponsorblock}",
            "sponsorblock_categories": [
                "outro",
                "selfpromo",
                "preview",
                "interaction",
                "sponsor",
                "music_offtopic",
                "intro",
            ],
            "remove_sponsorblock_categories": "all",
            "remove_chapters_regex": [
                "Intro",
                "Outro",
            ],
        },
        "overrides": {
            "music_video_artist": "JMC",
            "url": "https://your.name.here",
            "enable_sponsorblock": "False",
        },
    }


class TestChapters:
    def test_chapters_disabled_respected(
        self,
        config,
        subscription_name,
        sponsorblock_disabled_dict,
        output_directory,
        mock_download_collection_entries,
    ):
        subscription = Subscription.from_dict(
            config=config,
            preset_name=subscription_name,
            preset_dict=sponsorblock_disabled_dict,
        )

        with mock_download_collection_entries(
            is_youtube_channel=False, num_urls=1, is_extracted_audio=False, is_dry_run=True
        ):
            _ = subscription.download(dry_run=True)

        script = subscription.overrides.script
        assert script.get(ytdl_sub_chapters_from_comments.variable_name).native == ""