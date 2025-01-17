from ytdl_sub.config.overrides import Overrides
from ytdl_sub.entries.entry import Entry
from ytdl_sub.plugins.nfo_tags import NfoTagsValidator
from ytdl_sub.plugins.nfo_tags import SharedNfoTagsOptions
from ytdl_sub.plugins.nfo_tags import SharedNfoTagsPlugin
from ytdl_sub.validators.string_formatter_validators import StringFormatterValidator
from ytdl_sub.ytdl_additions.enhanced_download_archive import EnhancedDownloadArchive


class SeasonNfoTagsOptions(SharedNfoTagsOptions):
    """
    Adds a single NFO file in the season directory. An NFO file is simply an XML file with a
    ``.nfo`` extension. It uses the last entry's source variables which can change per download
    invocation. Be cautious of which variables you use.

    Usage:

    .. code-block:: yaml

       presets:
         my_example_preset:
           season_nfo_tags:
             # required
             nfo_name: "season.nfo"
             nfo_root: "season"
             tags:
               title: "My custom season name!"
             # optional
             kodi_safe: False
    """

    # Hack to make it so collection named seasons do not error
    # when adding output_directory_nfo info for plex
    _required_keys = set()
    _optional_keys = {"enable", "kodi_safe", "nfo_name", "nfo_root", "tags"}

    @property
    def nfo_root(self) -> StringFormatterValidator:
        """
        :expected type: EntryFormatter
        :description:
          The root tag of the NFO's XML. In the usage above, it would look like

          .. code-block:: xml

             <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
             <season>
             </season>
        """
        return self._nfo_root

    @property
    def tags(self) -> NfoTagsValidator:
        """
        :expected type: NfoTags
        :description:
          Tags within the nfo_root tag. In the usage above, it would look like

          .. code-block:: xml

             <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
             <season>
               <title>My custom season name!</title>
             </season>
        """
        return self._tags


class SeasonNfoTagsPlugin(SharedNfoTagsPlugin):
    plugin_options_type = SeasonNfoTagsOptions

    def __init__(
        self,
        options: SeasonNfoTagsOptions,
        overrides: Overrides,
        enhanced_download_archive: EnhancedDownloadArchive,
    ):
        super().__init__(options, overrides, enhanced_download_archive)
        self._created_output_nfo = False

    def post_process_entry(self, entry: Entry) -> None:
        """
        Creates an season NFO file using values defined by the season collection name
        """
        if (
            self.plugin_options.nfo_name is not None
            and self.plugin_options.nfo_root is not None
        ):
            self._create_nfo(entry=entry, save_to_entry=False)
            self._created_output_nfo = True
