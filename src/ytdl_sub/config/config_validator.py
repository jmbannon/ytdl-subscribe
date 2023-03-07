from typing import Any
from typing import Dict
from typing import Optional

from mergedeep import mergedeep
from yt_dlp.utils import datetime_from_str

from ytdl_sub.prebuilt_presets import PREBUILT_PRESETS
from ytdl_sub.utils.system import IS_WINDOWS
from ytdl_sub.validators.file_path_validators import FFmpegFileValidator
from ytdl_sub.validators.file_path_validators import FFprobeFileValidator
from ytdl_sub.validators.strict_dict_validator import StrictDictValidator
from ytdl_sub.validators.validators import LiteralDictValidator, BoolValidator
from ytdl_sub.validators.validators import StringValidator

if IS_WINDOWS:
    _DEFAULT_LOCK_DIRECTORY = ""  # Not supported in Windows
    _DEFAULT_FFMPEG_PATH = ".\\ffmpeg.exe"
    _DEFAULT_FFPROBE_PATH = ".\\ffprobe.exe"
else:
    _DEFAULT_LOCK_DIRECTORY = "/tmp"
    _DEFAULT_FFMPEG_PATH = "/usr/bin/ffmpeg"
    _DEFAULT_FFPROBE_PATH = "/usr/bin/ffprobe"

class PersistLogsValidator(StrictDictValidator):
    _required_keys = {"logs_directory"}
    _optional_keys = {"keep_logs_after", "keep_successful_logs"}

    def __init__(self, name: str, value: Any):
        super().__init__(name, value)

        self._logs_directory = self._validate_key(
            key="logs_directory", validator=StringValidator
        )

        self._keep_logs_after: Optional[str] = None
        if keep_logs_validator := self._validate_key_if_present(
            key="keep_logs_after", validator=StringValidator
        ):
            try:
                self._keep_logs_after = datetime_from_str(keep_logs_validator.value)
            except Exception as exc:
                raise self._validation_exception(f"Invalid datetime string: {str(exc)}")

        self._keep_successful_logs = self._validate_key(
            key="keep_successful_logs", validator=BoolValidator, default=True
        )

    @property
    def logs_directory(self) -> str:
        return self._logs_directory.value

    @property
    def keep_logs_after(self) -> Optional[str]:
        return self._keep_logs_after

    @property
    def keep_successful_logs(self) -> bool:
        return self._keep_successful_logs.value


class ConfigOptions(StrictDictValidator):
    _required_keys = {"working_directory"}
    _optional_keys = {"umask", "dl_aliases", "persist_logs", "lock_directory", "ffmpeg_path", "ffprobe_path"}

    def __init__(self, name: str, value: Any):
        super().__init__(name, value)

        self._working_directory = self._validate_key(
            key="working_directory", validator=StringValidator
        )
        self._umask = self._validate_key_if_present(
            key="umask", validator=StringValidator, default="022"
        )
        self._dl_aliases = self._validate_key_if_present(
            key="dl_aliases", validator=LiteralDictValidator
        )
        self._persist_logs = self._validate_key_if_present(
            key="persist_logs", validator=PersistLogsValidator
        )
        self._lock_directory = self._validate_key(
            key="lock_directory", validator=StringValidator, default=_DEFAULT_LOCK_DIRECTORY
        )
        self._ffmpeg_path = self._validate_key(
            key="ffmpeg_path", validator=FFmpegFileValidator, default=_DEFAULT_FFMPEG_PATH
        )
        self._ffprobe_path = self._validate_key(
            key="ffprobe_path", validator=FFprobeFileValidator, default=_DEFAULT_FFPROBE_PATH
        )

    @property
    def working_directory(self) -> str:
        """
        The directory to temporarily store downloaded files before moving them into their final
        directory.
        """
        return self._working_directory.value

    @property
    def umask(self) -> Optional[str]:
        """
        Optional. Umask (octal format) to apply to every created file. Defaults to "022".
        """
        return self._umask.value

    @property
    def dl_aliases(self) -> Optional[Dict[str, str]]:
        """
        .. _dl_aliases:

        Optional. Alias definitions to shorten ``ytdl-sub dl`` arguments. For example,

        .. code-block:: yaml

           configuration:
             dl_aliases:
               mv: "--preset music_video"
               u: "--download.url"

        Simplifies

        .. code-block:: bash

           ytdl-sub dl --preset "music_video" --download.url "youtube.com/watch?v=a1b2c3"

        to

        .. code-block:: bash

           ytdl-sub dl --mv --u "youtube.com/watch?v=a1b2c3"
        """
        if self._dl_aliases:
            return self._dl_aliases.dict
        return {}

    @property
    def persist_logs(self) -> Optional[PersistLogsValidator]:
        # TODO: nested docstring???
        return self._persist_logs

    @property
    def lock_directory(self) -> str:
        """
        Optional. The directory to temporarily store file locks, which prevents multiple instances
        of ``ytdl-sub`` from running. Note that file locks do not work on network-mounted
        directories. Ensure that this directory resides on the host machine. Defaults to ``/tmp``.
        """
        return self._lock_directory.value

    @property
    def ffmpeg_path(self) -> str:
        """
        Optional. Path to ffmpeg executable. Defaults to ``/usr/bin/ffmpeg`` for Linux, and
        ``ffmpeg.exe`` for Windows (in the same directory as ytdl-sub).
        """
        return self._ffmpeg_path.value

    @property
    def ffprobe_path(self) -> str:
        """
        Optional. Path to ffprobe executable. Defaults to ``/usr/bin/ffprobe`` for Linux, and
        ``ffprobe.exe`` for Windows (in the same directory as ytdl-sub).
        """
        return self._ffprobe_path.value


class ConfigValidator(StrictDictValidator):
    _required_keys = {"configuration", "presets"}

    def __init__(self, name: str, value: Any):
        super().__init__(name, value)
        self.config_options = self._validate_key("configuration", ConfigOptions)

        # Make sure presets is a dictionary. Will be validated in `PresetValidator`
        self.presets = self._validate_key("presets", LiteralDictValidator)

        # Ensure custom presets do not collide with prebuilt presets
        for preset_name in self.presets.keys:
            if preset_name in PREBUILT_PRESETS:
                raise self._validation_exception(
                    f"preset name '{preset_name}' conflicts with a prebuilt preset"
                )

        # Merge prebuilt presets into the config so custom presets can use them
        mergedeep.merge(self.presets._value, PREBUILT_PRESETS)
