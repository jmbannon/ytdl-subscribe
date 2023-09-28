import copy
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ytdl_sub.config.config_file import ConfigFile
from ytdl_sub.config.preset import Preset
from ytdl_sub.subscriptions.subscription_download import SubscriptionDownload
from ytdl_sub.subscriptions.subscription_validators import SubscriptionValidator
from ytdl_sub.utils.exceptions import ValidationException
from ytdl_sub.utils.yaml import load_yaml
from ytdl_sub.validators.validators import LiteralDictValidator

FILE_PRESET_APPLY_KEY = "__preset__"
FILE_SUBSCRIPTION_VALUE_KEY = "__value__"


class Subscription(SubscriptionDownload):
    @classmethod
    def from_preset(cls, preset: Preset, config: ConfigFile) -> "Subscription":
        """
        Creates a subscription from a preset

        Parameters
        ----------
        preset
            Preset to make the subscription out of
        config
            The config file that should contain this preset

        Returns
        -------
        Initialized subscription
        """
        return cls(
            name=preset.name,
            preset_options=preset,
            config_options=config.config_options,
        )

    @classmethod
    def from_dict(cls, config: ConfigFile, preset_name: str, preset_dict: Dict) -> "Subscription":
        """
        Creates a subscription from a preset dict

        Parameters
        ----------
        config:
            Validated instance of the config
        preset_name:
            Name of the preset
        preset_dict:
            The preset config in dict format

        Returns
        -------
        Initialized subscription
        """
        return cls.from_preset(
            preset=Preset.from_dict(
                config=config,
                preset_name=preset_name,
                preset_dict=preset_dict,
            ),
            config=config,
        )

    @classmethod
    def _maybe_get_subscription_value(
        cls, config: ConfigFile, subscription_dict: Dict
    ) -> Optional[str]:
        if FILE_SUBSCRIPTION_VALUE_KEY in subscription_dict:
            if not isinstance(subscription_dict[FILE_SUBSCRIPTION_VALUE_KEY], str):
                raise ValidationException(
                    f"Using {FILE_SUBSCRIPTION_VALUE_KEY} in a subscription"
                    f"must be a string that corresponds to an override variable"
                )
            return subscription_dict[FILE_SUBSCRIPTION_VALUE_KEY]

        return config.config_options.subscription_value  # can be None

    @classmethod
    def from_file_path(cls, config: ConfigFile, subscription_path: str) -> List["Subscription"]:
        """
        Loads subscriptions from a file and applies ``__preset__`` to all of them if present.
        If a subscription is in the form of key: value, it will set value to the override
        variable defined in ``__value__``.

        Parameters
        ----------
        config:
            Validated instance of the config
        subscription_path:
            File path to the subscription yaml file

        Returns
        -------
        List of subscriptions, for each one in the subscription yaml

        Raises
        ------
        ValidationException
            If subscription file is misconfigured
        """
        subscriptions: List["Subscription"] = []
        subscription_dict = load_yaml(file_path=subscription_path)

        has_file_preset = FILE_PRESET_APPLY_KEY in subscription_dict
        file_subscription_value: Optional[str] = cls._maybe_get_subscription_value(
            config=config, subscription_dict=subscription_dict
        )

        # If a file preset is present...
        if has_file_preset:
            # Validate it (make sure it is a dict)
            file_preset = LiteralDictValidator(
                name=f"{subscription_path}.{FILE_PRESET_APPLY_KEY}",
                value=subscription_dict[FILE_PRESET_APPLY_KEY],
            )

            # Deep copy the config and add this file preset to its preset list
            config = copy.deepcopy(config)
            config.presets.dict[FILE_PRESET_APPLY_KEY] = file_preset.dict

        subscriptions_dict: Dict[str, Any] = {
            key: obj
            for key, obj in subscription_dict.items()
            if key not in [FILE_PRESET_APPLY_KEY, FILE_SUBSCRIPTION_VALUE_KEY]
        }

        subscriptions_dicts = SubscriptionValidator(
            name="",
            value=subscriptions_dict,
            config=config,
            presets=[FILE_PRESET_APPLY_KEY] if has_file_preset else [],
            subscription_value=file_subscription_value,
        ).subscription_dicts()

        for subscription_key, subscription_object in subscriptions_dicts.items():
            subscriptions.append(
                cls.from_dict(
                    config=config,
                    preset_name=subscription_key,
                    preset_dict=subscription_object,
                )
            )

        return subscriptions
