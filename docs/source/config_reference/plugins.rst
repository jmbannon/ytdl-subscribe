
Plugins
=======

audio_extract
-------------
Extracts audio from a video file.

:Usage:

.. code-block:: yaml

   audio_extract:
     codec: "mp3"
     quality: 128

``codec``

:expected type: String
:description:
  The codec to output after extracting the audio. Supported codecs are aac, flac, mp3, m4a,
  opus, vorbis, wav, and best to grab the best possible format at runtime.


``enable``

:expected type: Optional[OverridesFormatter]
:description:
  Can typically be left undefined to always default to enable. For preset convenience,
  this field can be set using an override variable to easily toggle whether this plugin
  is enabled or not via Boolean.


``quality``

:expected type: Float
:description:
  Optional. Specify ffmpeg audio quality. Insert a value between ``0`` (better) and ``9``
  (worse) for variable bitrate, or a specific bitrate like ``128`` for 128k.


----------------------------------------------------------------------------------------------------

chapters
--------
Embeds chapters to video files if they are present. Additional options to add SponsorBlock
chapters and remove specific ones. Can also remove chapters using regex.

:Usage:

.. code-block:: yaml

   chapters:
     # Embedded Chapter Fields
     embed_chapters: True
     allow_chapters_from_comments: False
     remove_chapters_regex:
       - "Intro"
       - "Outro"

     # Sponsorblock Fields
     sponsorblock_categories:
       - "outro"
       - "selfpromo"
       - "preview"
       - "interaction"
       - "sponsor"
       - "music_offtopic"
       - "intro"
     remove_sponsorblock_categories: "all"
     force_key_frames: False

``allow_chapters_from_comments``

:expected type: Optional[Boolean]
:description:
  Defaults to False. If chapters do not exist in the video/description itself, attempt to
  scrape comments to find the chapters.


``embed_chapters``

:expected type: Optional[Boolean]
:description:
  Defaults to True. Embed chapters into the file.


``enable``

:expected type: Optional[OverridesFormatter]
:description:
  Can typically be left undefined to always default to enable. For preset convenience,
  this field can be set using an override variable to easily toggle whether this plugin
  is enabled or not via Boolean.


``force_key_frames``

:expected type: Optional[Boolean]
:description:
  Defaults to False. Force keyframes at cuts when removing sections. This is slow due to
  needing a re-encode, but the resulting video may have fewer artifacts around the cuts.


``remove_chapters_regex``

:expected type: Optional[List[RegexString]
:description:
  List of regex patterns to match chapter titles against and remove them from the
  entry.


``remove_sponsorblock_categories``

:expected type: Optional[List[String]]
:description:
  List of SponsorBlock categories to remove from the output file. Can only remove
  categories that are specified in ``sponsorblock_categories`` or "all", which removes
  everything specified in ``sponsorblock_categories``.


``sponsorblock_categories``

:expected type: Optional[List[String]]
:description:
  List of SponsorBlock categories to embed as chapters. Supports "sponsor",
  "intro", "outro", "selfpromo", "preview", "filler", "interaction", "music_offtopic",
  "poi_highlight", or "all" to include all categories.


----------------------------------------------------------------------------------------------------

date_range
----------
Only download files uploaded within the specified date range.
Dates must adhere to a yt-dlp datetime. From their docs:

.. code-block:: Markdown

   A string in the format YYYYMMDD or
   (now|today|yesterday|date)[+-][0-9](microsecond|second|minute|hour|day|week|month|year)(s)

Valid examples are ``now-2weeks`` or ``20200101``. Can use override variables in this.
Note that yt-dlp will round times to the closest day, meaning that `day` is the lowest
granularity possible.

:Usage:

.. code-block:: yaml

   date_range:
     before: "now"
     after: "today-2weeks"

``after``

:expected type: Optional[OverridesFormatter]
:description:
  Only download videos after this datetime.


``before``

:expected type: Optional[OverridesFormatter]
:description:
  Only download videos before this datetime.


``breaks``

:expected type: Optional[OverridesFormatter]
:description:
  Toggle to enable breaking subsequent metadata downloads if an entry's upload date
  is out of range. Defaults to True.


``enable``

:expected type: Optional[OverridesFormatter]
:description:
  Can typically be left undefined to always default to enable. For preset convenience,
  this field can be set using an override variable to easily toggle whether this plugin
  is enabled or not via Boolean.


----------------------------------------------------------------------------------------------------

download
--------
Sets the URL(s) to download from. Can be used in many forms, including

:Single URL:

.. code-block:: yaml

   download: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

:Multi URL:

.. code-block:: yaml

   download:
     - "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
     - "https://www.youtube.com/watch?v=3BFTio5296w"

:Thumbnails + Variables:

All variables must be defined for the top-most url. All subsequent URL variables can be either
overwritten or default to the top-most value.

If an entry is returned from more than one URL, it will use the variables in the bottom-most
URL.

.. code-block:: yaml

  download:
    # required
    urls:
      - url: "youtube.com/channel/UCsvn_Po0SmunchJYtttWpOxMg"
        variables:
          season_index: "1"
          season_name: "Uploads"
        playlist_thumbnails:
          - name: "poster.jpg"
            uid: "avatar_uncropped"
          - name: "fanart.jpg"
            uid: "banner_uncropped"
          - name: "season{season_index}-poster.jpg"
            uid: "latest_entry"
      - url: "https://www.youtube.com/playlist?list=UCsvn_Po0SmunchJYtttWpOxMg"
        variables:
          season_index: "2"
          season_name: "Playlist as Season"
        ytdl_options:
          break_on_existing: False
        playlist_thumbnails:
          - name: "season{season_index}-poster.jpg"
            uid: "latest_entry"

----------------------------------------------------------------------------------------------------

embed_thumbnail
---------------
Whether to embed thumbnails to the audio/video file or not.

:Usage:

.. code-block:: yaml

   embed_thumbnail: True

----------------------------------------------------------------------------------------------------

file_convert
------------
Converts video files from one extension to another.

:Usage:

.. code-block:: yaml

   file_convert:
     convert_to: "mp4"

Also supports custom ffmpeg conversions:

:Usage:

.. code-block:: yaml

   file_convert:
     convert_to: "mkv"
     convert_with: "ffmpeg"
     ffmpeg_post_process_args: >
       -bitexact
       -vcodec copy
       -acodec copy
       -scodec mov_text

``convert_to``

:expected type: String
:description:
  Convert to a desired file type. Supports

    - Video: avi, flv, mkv, mov, mp4, webm
    - Audio: aac, flac, mp3, m4a, opus, vorbis, wav


``convert_with``

:expected type: Optional[String]
:description:
  Supports ``yt-dlp`` and ``ffmpeg``. ``yt-dlp`` will convert files within
  yt-dlp whereas ``ffmpeg`` specifies it will be converted using a custom command specified
  with ``ffmpeg_post_process_args``. Defaults to ``yt-dlp``.


``enable``

:expected type: Optional[OverridesFormatter]
:description:
  Can typically be left undefined to always default to enable. For preset convenience,
  this field can be set using an override variable to easily toggle whether this plugin
  is enabled or not via Boolean.


``ffmpeg_post_process_args``

:expected type: Optional[OverridesFormatter]
:description:
  ffmpeg args to post-process an entry file with. The args will be inserted in the
  form of

  ``ffmpeg -i input_file.ext {ffmpeg_post_process_args) output_file.output_ext``.

  The output file will use the extension specified in ``convert_to``. Post-processing args
  can still be set  with ``convert_with`` set to ``yt-dlp``.


----------------------------------------------------------------------------------------------------

filter_exclude
--------------
Applies a conditional OR on any number of filters comprised of either variables or scripts.
If any filter evaluates to True, the entry will be excluded.

:Usage:

.. code-block:: yaml

   filter_exclude:
     - >-
       { %contains( %lower(title), '#short' ) }
     - >-
       { %contains( %lower(description), '#short' ) }

----------------------------------------------------------------------------------------------------

filter_include
--------------
Applies a conditional AND on any number of filters comprised of either variables or scripts.
If all filters evaluate to True, the entry will be included.

:Usage:

.. code-block:: yaml

   filter_include:
     - >-
       {description}
     - >-
       {
         %regex_search_any(
            title,
            [
                "Full Episode",
                "FULL",
            ]
         )
       }

----------------------------------------------------------------------------------------------------

format
------
Set ``--format`` to pass into yt-dlp to download a specific format quality.
Uses the same syntax as yt-dlp.

Usage:

.. code-block:: yaml

   format: "(bv*[height<=1080]+bestaudio/best[height<=1080])"

----------------------------------------------------------------------------------------------------

match_filters
-------------
Set ``--match-filters`` to pass into yt-dlp to filter entries from being downloaded.
Uses the same syntax as yt-dlp. An entry will be downloaded if any one of the filters are met.
For logical AND's between match filters, use the ``&`` operator in a single match filter.

:Usage:

.. code-block:: yaml

   match_filters:
     filters:
       - "age_limit<?18 & like_count>?100"
       # Other common match-filters
       # - "original_url!*=/shorts/ & !is_live"
       # - "availability=?public"

----------------------------------------------------------------------------------------------------

music_tags
----------
Adds tags to every download audio file using
`MediaFile <https://mediafile.readthedocs.io/en/latest/>`_,
the same audio file tagging package used by
`beets <https://beets.readthedocs.io/en/stable/>`_.
It supports basic tags like ``title``, ``album``, ``artist`` and ``albumartist``. You can find
a full list of tags for various file types in MediaFile's
`source code <https://github.com/beetbox/mediafile/blob/v0.9.0/mediafile.py#L1770>`_.

Note that the date fields ``date`` and ``original_date`` expected a standardized date in the
form of YYYY-MM-DD. The variable ``upload_date_standardized`` returns a compatible format.

:Usage:

.. code-block:: yaml

   presets:
     my_example_preset:
       music_tags:
         artist: "{artist}"
         album: "{album}"
         # Supports id3v2.4 multi-tags
         genres:
           - "{genre}"
           - "ytdl-sub"
         albumartists:
           - "{artist}"
           - "ytdl-sub"
         date: "{upload_date_standardized}"

----------------------------------------------------------------------------------------------------

nfo_tags
--------
Adds an NFO file for every download file. An NFO file is simply an XML file
with a ``.nfo`` extension. You can add any values into the NFO.

:Usage:

.. code-block:: yaml

   nfo_tags:
     nfo_name: "{title_sanitized}.nfo"
     nfo_root: "episodedetails"
     tags:
       title: "{title}"
       season: "{upload_year}"
       episode: "{upload_month}{upload_day_padded}"
     kodi_safe: False

``enable``

:expected type: Optional[OverridesFormatter]
:description:
  Can typically be left undefined to always default to enable. For preset convenience,
  this field can be set using an override variable to easily toggle whether this plugin
  is enabled or not via Boolean.


``kodi_safe``

:expected type: Optional[Boolean]
:description:
  Defaults to False. Kodi does not support > 3-byte unicode characters, which include
  emojis and some foreign language characters. Setting this to True will replace those
  characters with '□'.


``nfo_name``

:expected type: EntryFormatter
:description:
  The NFO file name.


``nfo_root``

:expected type: EntryFormatter
:description:
  The root tag of the NFO's XML. In the usage above, it would look like

  .. code-block:: xml

     <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
     <episodedetails>
     </episodedetails>


``tags``

:expected type: NfoTags
:description:
  Tags within the nfo_root tag. In the usage above, it would look like

  .. code-block:: xml

     <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
     <episodedetails>
       <title>Awesome Youtube Video</title>
       <season>2022</season>
       <episode>502</episode>
     </episodedetails>

  Also supports xml attributes and duplicate keys:

  .. code-block:: yaml

     tags:
       season:
         attributes:
           name: "Best Year"
         tag: "{upload_year}"
       genre:
         - "Comedy"
         - "Drama"

  Which translates to

  .. code-block:: xml

     <season name="Best Year">2022</season>
     <genre>Comedy</genre>
     <genre>Drama</genre>


----------------------------------------------------------------------------------------------------

output_directory_nfo_tags
-------------------------
Adds a single NFO file in the output directory. An NFO file is simply an XML file with a
``.nfo`` extension. It uses the last entry's source variables which can change per download
invocation. Be cautious of which variables you use.

Usage:

.. code-block:: yaml

   presets:
     my_example_preset:
       output_directory_nfo_tags:
         # required
         nfo_name: "tvshow.nfo"
         nfo_root: "tvshow"
         tags:
           title: "Sweet youtube TV show"
         # optional
         kodi_safe: False

``enable``

:expected type: Optional[OverridesFormatter]
:description:
  Can typically be left undefined to always default to enable. For preset convenience,
  this field can be set using an override variable to easily toggle whether this plugin
  is enabled or not via Boolean.


``kodi_safe``

:expected type: Optional[Boolean]
:description:
  Defaults to False. Kodi does not support > 3-byte unicode characters, which include
  emojis and some foreign language characters. Setting this to True will replace those
  characters with '□'.


``nfo_name``

:expected type: EntryFormatter
:description:
  The NFO file name.


``nfo_root``

:expected type: EntryFormatter
:description:
  The root tag of the NFO's XML. In the usage above, it would look like

  .. code-block:: xml

     <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
     <tvshow>
     </tvshow>


``tags``

:expected type: NfoTags
:description:
  Tags within the nfo_root tag. In the usage above, it would look like

  .. code-block:: xml

     <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
     <tvshow>
       <title>Sweet youtube TV show</title>
     </tvshow>

  Also supports xml attributes and duplicate keys:

  .. code-block:: yaml

     tags:
       named_season:
         - tag: "{source_title}"
           attributes:
             number: "{collection_index}"
       genre:
         - "Comedy"
         - "Drama"

  Which translates to

  .. code-block:: xml

     <title year="2022">Sweet youtube TV show</season>
     <genre>Comedy</genre>
     <genre>Drama</genre>


----------------------------------------------------------------------------------------------------

output_options
--------------
Defines where to output files and thumbnails after all post-processing has completed.

:Usage:

.. code-block:: yaml

   presets:
     my_example_preset:
       output_options:
         # required
         output_directory: "/path/to/videos_or_music"
         file_name: "{title_sanitized}.{ext}"
         # optional
         thumbnail_name: "{title_sanitized}.{thumbnail_ext}"
         info_json_name: "{title_sanitized}.{info_json_ext}"
         download_archive_name: ".ytdl-sub-{subscription_name}-download-archive.json"
         migrated_download_archive_name: ".ytdl-sub-{subscription_name_sanitized}-download-archive.json"
         maintain_download_archive: True
         keep_files_before: now
         keep_files_after: 19000101

``download_archive_name``

:expected type: Optional[OverridesFormatter]
:description:
  The file name to store a subscriptions download archive placed relative to
  the output directory. Defaults to ``.ytdl-sub-{subscription_name}-download-archive.json``


``file_name``

:expected type: EntryFormatter
:description:
  The file name for the media file. This can include directories such as
  ``"Season {upload_year}/{title}.{ext}"``, and will be placed in the output directory.


``info_json_name``

:expected type: Optional[EntryFormatter]
:description:
  The file name for the media's info json file. This can include directories such
  as ``"Season {upload_year}/{title}.{info_json_ext}"``, and will be placed in the output
  directory. Can be set to empty string or `null` to disable info json writes.


``keep_files_after``

:expected type: Optional[OverridesFormatter]
:description:
  Requires ``maintain_download_archive`` set to True. Uses the same syntax as the
  ``date_range`` plugin.

  Only keeps files that are uploaded after this datetime. By default, ytdl-sub will keep
  files after ``19000101``, which implies all files. Can be used in conjunction with
  ``keep_max_files``.


``keep_files_before``

:expected type: Optional[OverridesFormatter]
:description:
  Requires ``maintain_download_archive`` set to True. Uses the same syntax as the
  ``date_range`` plugin.

  Only keeps files that are uploaded before this datetime. By default, ytdl-sub will keep
  files before ``now``, which implies all files. Can be used in conjunction with
  ``keep_max_files``.


``keep_max_files``

:expected type: Optional[OverridesFormatter]
:description:
  Requires ``maintain_download_archive`` set to True.

  Only keeps N most recently uploaded videos. If set to <= 0, ``keep_max_files`` will not be
  applied. Can be used in conjunction with ``keep_files_before`` and ``keep_files_after``.


``maintain_download_archive``

:expected type: Optional[Boolean]
:description:
  Maintains a download archive file in the output directory for a subscription.
  It is named ``.ytdl-sub-{subscription_name}-download-archive.json``, stored in the
  output directory.

  The download archive contains a mapping of ytdl IDs to downloaded files. This is used to
  create a ytdl download-archive file when invoking a download on a subscription. This will
  prevent ytdl from redownloading media already downloaded.

  Defaults to False.


``migrated_download_archive_name``

:expected type: Optional[OverridesFormatter]
:description:
  Intended to be used if you are migrating a subscription with either a new
  subscription name or output directory. It will try to load the archive file using this
  name first, and fallback to ``download_archive_name``. It will always save to this file
  and remove the original ``download_archive_name``.


``output_directory``

:expected type: OverridesFormatter
:description:
  The output directory to store all media files downloaded.


``thumbnail_name``

:expected type: Optional[EntryFormatter]
:description:
  The file name for the media's thumbnail image. This can include directories such
  as ``"Season {upload_year}/{title}.{thumbnail_ext}"``, and will be placed in the output
  directory. Can be set to empty string or `null` to disable thumbnail writes.


----------------------------------------------------------------------------------------------------

overrides
---------
Allows you to define variables that can be used in any EntryFormatter or OverridesFormatter.

:Usage:

.. code-block:: yaml

   presets:
     my_example_preset:
       overrides:
         output_directory: "/path/to/media"
         custom_file_name: "{upload_date_standardized}.{title_sanitized}"

       # Then use the override variables in the output options
       output_options:
         output_directory: "{output_directory}"
         file_name: "{custom_file_name}.{ext}"
         thumbnail_name: "{custom_file_name}.{thumbnail_ext}"

Override variables can contain explicit values and other variables, including both override
and source variables.

In addition, any override variable defined will automatically create a ``sanitized`` variable
for use. In the example above, ``output_directory_sanitized`` will exist and perform
sanitization on the value when used.

----------------------------------------------------------------------------------------------------

season_nfo_tags
---------------
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

``enable``

:expected type: Optional[OverridesFormatter]
:description:
  Can typically be left undefined to always default to enable. For preset convenience,
  this field can be set using an override variable to easily toggle whether this plugin
  is enabled or not via Boolean.


``kodi_safe``

:expected type: Optional[Boolean]
:description:
  Defaults to False. Kodi does not support > 3-byte unicode characters, which include
  emojis and some foreign language characters. Setting this to True will replace those
  characters with '□'.


``nfo_name``

:expected type: EntryFormatter
:description:
  The NFO file name.


``nfo_root``

:expected type: EntryFormatter
:description:
  The root tag of the NFO's XML. In the usage above, it would look like

  .. code-block:: xml

     <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
     <season>
     </season>


``tags``

:expected type: NfoTags
:description:
  Tags within the nfo_root tag. In the usage above, it would look like

  .. code-block:: xml

     <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
     <season>
       <title>My custom season name!</title>
     </season>


----------------------------------------------------------------------------------------------------

split_by_chapters
-----------------
Splits a file by chapters into multiple files. Each file becomes its own entry with the
new variables

  - ``chapter_title``
  - ``chapter_index``
  - ``chapter_index_padded``
  - ``chapter_count``

Note that when using this plugin and performing dry-run, it assumes embedded chapters are being
used with no modifications.

:Usage:

.. code-block:: yaml

   split_by_chapters:
     when_no_chapters: "pass"

``when_no_chapters``

:expected type: String
:description:
  Behavior to perform when no chapters are present. Supports

    - "pass" (continue processing),
    - "drop" (exclude it from output)
    - "error" (stop processing for everything).

  If a file has no chapters and is set to "pass", then ``chapter_title`` is
  set to the entry's title and ``chapter_index``, ``chapter_count`` are both set to 1.


----------------------------------------------------------------------------------------------------

subtitles
---------
Defines how to download and store subtitles. Using this plugin creates two new variables:
``lang`` and ``subtitles_ext``. ``lang`` is dynamic since you can download multiple subtitles.
It will set the respective language to the correct subtitle file.

:Usage:

.. code-block:: yaml

   subtitles:
     subtitles_name: "{title_sanitized}.{lang}.{subtitles_ext}"
     subtitles_type: "srt"
     embed_subtitles: False
     languages:
       - "en"  # supports multiple languages
       - "de"
     allow_auto_generated_subtitles: False

``allow_auto_generated_subtitles``

:expected type: Optional[Boolean]
:description:
  Defaults to False. Whether to allow auto generated subtitles.


``embed_subtitles``

:expected type: Optional[Boolean]
:description:
  Defaults to False. Whether to embed the subtitles into the video file. Note that
  webm files can only embed "vtt" subtitle types.


``enable``

:expected type: Optional[OverridesFormatter]
:description:
  Can typically be left undefined to always default to enable. For preset convenience,
  this field can be set using an override variable to easily toggle whether this plugin
  is enabled or not via Boolean.


``languages``

:expected type: Optional[List[String]]
:description:
  Language code(s) to download for subtitles. Supports a single or list of multiple
  language codes. Defaults to only "en".


``subtitles_name``

:expected type: Optional[EntryFormatter]
:description:
  The file name for the media's subtitles if they are present. This can include
  directories such as ``"Season {upload_year}/{title_sanitized}.{lang}.{subtitles_ext}"``,
  and will be placed in the output directory. ``lang`` is dynamic since you can download
  multiple subtitles. It will set the respective language to the correct subtitle file.


``subtitles_type``

:expected type: Optional[String]
:description:
  Defaults to "srt". One of the subtitle file types "srt", "vtt", "ass", "lrc".


----------------------------------------------------------------------------------------------------

throttle_protection
-------------------
Provides options to make ytdl-sub look more 'human-like' to protect from throttling. For
range-based values, a random number will be chosen within the range to avoid sleeps looking
scripted.

:Usage:

.. code-block:: yaml

   presets:
     my_example_preset:
       throttle_protection:
         sleep_per_download_s:
           min: 2.2
           max: 10.8
         sleep_per_subscription_s:
           min: 9.0
           max: 14.1
         max_downloads_per_subscription:
           min: 10
           max: 36
         subscription_download_probability: 1.0

``enable``

:expected type: Optional[OverridesFormatter]
:description:
  Can typically be left undefined to always default to enable. For preset convenience,
  this field can be set using an override variable to easily toggle whether this plugin
  is enabled or not via Boolean.


``max_downloads_per_subscription``

:expected type: Optional[Range]
:description:
  Number of downloads to perform per subscription.


``sleep_per_download_s``

:expected type: Optional[Range]
:description:
  Number in seconds to sleep between each download. Does not include time it takes for
  ytdl-sub to perform post-processing.


``sleep_per_subscription_s``

:expected type: Optional[Range]
:description:
  Number in seconds to sleep between each subscription.


``subscription_download_probability``

:expected type: Optional[Float]
:description:
  Probability to perform any downloads, recomputed for each subscription. This is only
  recommended to set if you run ytdl-sub in a cron-job, that way you are statistically
  guaranteed over time to eventually download the subscription.


----------------------------------------------------------------------------------------------------

video_tags
----------
Adds tags to every downloaded video file using ffmpeg ``-metadata key=value`` args.

:Usage:

.. code-block:: yaml

   video_tags:
     title: "{title}"
     date: "{upload_date}"
     description: "{description}"

----------------------------------------------------------------------------------------------------

ytdl_options
------------
Allows you to add any ytdl argument to ytdl-sub's downloader.
The argument names can differ slightly from the command-line argument names. See
`this docstring <https://github.com/yt-dlp/yt-dlp/blob/2022.04.08/yt_dlp/YoutubeDL.py#L197>`_
for more details.

:Usage:

.. code-block:: yaml

       presets:
         my_example_preset:
           ytdl_options:
             # Ignore any download related errors and continue
             ignoreerrors: True
             # Stop downloading additional metadata/videos if it
             # exists in your download archive
             break_on_existing: True
             # Path to your YouTube cookies file to download 18+ restricted content
             cookiefile: "/path/to/cookies/file.txt"
             # Only download this number of videos/audio
             max_downloads: 10
             # Download and use English title/description/etc YouTube metadata
             extractor_args:
               youtube:
                 lang:
                   - "en"


where each key is a ytdl argument. Include in the example are some popular ytdl_options.
