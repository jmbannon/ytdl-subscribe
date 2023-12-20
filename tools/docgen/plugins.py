import inspect
from typing import Dict
from typing import Type

from tools.docgen.utils import section
from ytdl_sub.config.overrides import Overrides
from ytdl_sub.config.plugin.plugin_mapping import PluginMapping
from ytdl_sub.config.preset_options import OutputOptions
from ytdl_sub.config.preset_options import YTDLOptions
from ytdl_sub.config.validators.options import OptionsValidator


def should_filter_property(property_name: str) -> bool:
    return property_name.startswith("_") or property_name in (
        "value",
        "source_variable_capture_dict",
        "dict",
        "keys",
        "dict_with_format_strings",
        "subscription_name",
    )


def generate_plugin_docs(name: str, options: Type[OptionsValidator], offset: int):
    docs = ""
    docs += section(name, level=offset + 0)

    docs += inspect.cleandoc(options.__doc__)
    docs += "\n"

    property_names = [
        prop
        for prop in dir(options)
        if isinstance(getattr(options, prop), property) and not should_filter_property(prop)
    ]
    for property_name in sorted(property_names):
        docs += section(property_name, level=offset + 1)
        docs += inspect.cleandoc(getattr(options, property_name).__doc__)
        docs += "\n"

    return docs


def generate_plugin_rst():
    options_dict: Dict[str, Type[OptionsValidator]] = {
        "output_options": OutputOptions,
        "ytdl_options": YTDLOptions,
        "overrides": Overrides,
    }
    for plugin_name, plugin_type in PluginMapping._MAPPING.items():
        if plugin_name.startswith("_"):
            continue
        options_dict[plugin_name] = plugin_type.plugin_options_type

    docs = section("Plugins", level=0)
    for name in sorted(options_dict.keys()):
        docs += generate_plugin_docs(name, options_dict[name], offset=1)

    return docs


print(generate_plugin_rst())
