from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type

from ytdl_sub.config.plugin.plugin import Plugin
from ytdl_sub.config.plugin.plugin import SplitPlugin
from ytdl_sub.config.plugin.plugin_operation import PluginOperation
from ytdl_sub.config.validators.options import OptionsValidator
from ytdl_sub.downloaders.url.downloader import UrlDownloaderCollectionVariablePlugin
from ytdl_sub.downloaders.url.downloader import UrlDownloaderThumbnailPlugin
from ytdl_sub.plugins.audio_extract import AudioExtractPlugin
from ytdl_sub.plugins.chapters import ChaptersPlugin
from ytdl_sub.plugins.date_range import DateRangePlugin
from ytdl_sub.plugins.embed_thumbnail import EmbedThumbnailPlugin
from ytdl_sub.plugins.file_convert import FileConvertPlugin
from ytdl_sub.plugins.filter_exclude import FilterExcludePlugin
from ytdl_sub.plugins.filter_include import FilterIncludePlugin
from ytdl_sub.plugins.format import FormatPlugin
from ytdl_sub.plugins.internal.view import ViewPlugin
from ytdl_sub.plugins.match_filters import MatchFiltersPlugin
from ytdl_sub.plugins.music_tags import MusicTagsPlugin
from ytdl_sub.plugins.nfo_tags import NfoTagsPlugin
from ytdl_sub.plugins.output_directory_nfo_tags import OutputDirectoryNfoTagsPlugin
from ytdl_sub.plugins.season_nfo_tags import SeasonNfoTagsPlugin
from ytdl_sub.plugins.split_by_chapters import SplitByChaptersPlugin
from ytdl_sub.plugins.subtitles import SubtitlesPlugin
from ytdl_sub.plugins.throttle_protection import ThrottleProtectionPlugin
from ytdl_sub.plugins.video_tags import VideoTagsPlugin


class PluginMapping:
    """
    Maps plugins defined in the preset to its respective plugin class
    """

    _MAPPING: Dict[str, Type[Plugin]] = {
        "_view": ViewPlugin,
        "audio_extract": AudioExtractPlugin,
        "date_range": DateRangePlugin,
        "embed_thumbnail": EmbedThumbnailPlugin,
        "file_convert": FileConvertPlugin,
        "format": FormatPlugin,
        "match_filters": MatchFiltersPlugin,
        "music_tags": MusicTagsPlugin,
        "video_tags": VideoTagsPlugin,
        "nfo_tags": NfoTagsPlugin,
        "output_directory_nfo_tags": OutputDirectoryNfoTagsPlugin,
        "season_nfo_tags": SeasonNfoTagsPlugin,
        "subtitles": SubtitlesPlugin,
        "chapters": ChaptersPlugin,
        "split_by_chapters": SplitByChaptersPlugin,
        "throttle_protection": ThrottleProtectionPlugin,
        "filter_include": FilterIncludePlugin,
        "filter_exclude": FilterExcludePlugin,
    }

    # All other plugins are added after the defined ordered ones
    _ORDER_MODIFY_ENTRY_METADATA: List[Type[Plugin]] = [
        ThrottleProtectionPlugin,
        UrlDownloaderCollectionVariablePlugin,
        SubtitlesPlugin,
        FilterExcludePlugin,
        FilterIncludePlugin,
        # add all others
    ]

    _ORDER_MODIFY_ENTRY: List[Type[Plugin]] = [
        UrlDownloaderThumbnailPlugin,
        AudioExtractPlugin,
        FileConvertPlugin,
        ChaptersPlugin,
        SplitByChaptersPlugin,
        FilterExcludePlugin,
        FilterIncludePlugin,
        # add all others
    ]

    _ORDER_POST_PROCESS: List[Type[Plugin]] = [
        AudioExtractPlugin,
        FileConvertPlugin,
        ChaptersPlugin,
        SubtitlesPlugin,
        MusicTagsPlugin,
        VideoTagsPlugin,
        NfoTagsPlugin,
        SeasonNfoTagsPlugin,
        EmbedThumbnailPlugin,
    ]

    @classmethod
    def _order_by(
        cls, plugin_types: List[Type[Plugin]], operation: PluginOperation
    ) -> List[Type[Plugin]]:
        if operation == PluginOperation.MODIFY_ENTRY_METADATA:
            ordering = cls._ORDER_MODIFY_ENTRY_METADATA
        elif operation == PluginOperation.MODIFY_ENTRY:
            ordering = cls._ORDER_MODIFY_ENTRY
        elif operation == PluginOperation.POST_PROCESS:
            ordering = cls._ORDER_POST_PROCESS
        else:
            raise ValueError("PluginOperation does not support ordering")

        ordered_plugin_operations: List[Type[Plugin]] = []
        for pl_type in reversed(ordering):
            for plugin_type in plugin_types:
                if plugin_type == pl_type:
                    ordered_plugin_operations.insert(0, plugin_type)
                else:
                    ordered_plugin_operations.append(plugin_type)

        return ordered_plugin_operations

    @classmethod
    def order_options_by(
        cls, zipped: List[Tuple[Type[Plugin], OptionsValidator]], operation: PluginOperation
    ) -> List[OptionsValidator]:
        """
        Returns
        -------
        Ordered plugin options with respect to the PluginOperation.
        """
        ordered_types: List[Type[Plugin]] = cls._order_by(
            plugin_types=[val[0] for val in zipped], operation=operation
        )

        ordered_options: List[OptionsValidator] = []
        for plugin_type, plugin_options in zipped:
            sorted_idx = ordered_types.index(plugin_type)
            ordered_options.insert(sorted_idx, plugin_options)

        return ordered_options

    @classmethod
    def _is_modified_after_split(cls, plugin: Plugin) -> bool:
        if type(plugin) not in cls._ORDER_MODIFY_ENTRY:
            return True
        return cls._ORDER_MODIFY_ENTRY.index(type(plugin)) > cls._ORDER_MODIFY_ENTRY.index(
            SplitByChaptersPlugin
        )

    @classmethod
    def order_plugins_by(
        cls, plugins: List[Plugin], operation: PluginOperation, before_split: Optional[bool] = None
    ) -> List[Plugin]:
        """
        Returns
        -------
        Ordered plugins with respect to the PluginOperation. Optionally only return plugins
        before/after a split plugin.
        """
        ordered_types: List[Type[Plugin]] = cls._order_by(
            plugin_types=[type(plugin) for plugin in plugins], operation=operation
        )

        ordered_plugins: List[Plugin] = []
        for plugin in plugins:
            sorted_idx = ordered_types.index(type(plugin))
            ordered_plugins.insert(sorted_idx, plugin)

        if before_split is None:
            return ordered_plugins

        # Remove the split plugin if differentiating
        ordered_plugins = [
            plugin for plugin in ordered_plugins if not isinstance(plugin, SplitPlugin)
        ]
        if before_split:
            return [
                plugin for plugin in ordered_plugins if not cls._is_modified_after_split(plugin)
            ]

        # before_split is False
        return [plugin for plugin in ordered_plugins if cls._is_modified_after_split(plugin)]

    @classmethod
    def plugins(cls) -> List[str]:
        """
        Returns
        -------
        Available download sources
        """
        return sorted(list(cls._MAPPING.keys()))

    @classmethod
    def get(cls, plugin: str) -> Type[Plugin]:
        """
        Parameters
        ----------
        plugin
            Name of the plugin

        Returns
        -------
        The plugin class

        Raises
        ------
        ValueError
            Raised if the plugin does not exist
        """
        if plugin not in cls.plugins():
            raise ValueError(
                f"Tried to use plugin '{plugin}' that does not exist. Available plugins: "
                f"{', '.join(cls.plugins())}"
            )
        return cls._MAPPING[plugin]
