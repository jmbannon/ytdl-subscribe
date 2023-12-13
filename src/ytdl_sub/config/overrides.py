from typing import Any
from typing import Dict
from typing import Optional
from typing import Set

import mergedeep

from ytdl_sub.entries.entry import Entry
from ytdl_sub.entries.script.variable_definitions import VARIABLES
from ytdl_sub.entries.variables.override_variables import SUBSCRIPTION_NAME
from ytdl_sub.script.parser import parse
from ytdl_sub.script.script import Script
from ytdl_sub.utils.script import ScriptUtils
from ytdl_sub.utils.scriptable import Scriptable
from ytdl_sub.validators.string_formatter_validators import DictFormatterValidator
from ytdl_sub.validators.string_formatter_validators import StringFormatterValidator


class Overrides(DictFormatterValidator, Scriptable):
    """
    Optional. This section allows you to define variables that can be used in any string formatter.
    For example, if you want your file and thumbnail files to match without copy-pasting a large
    format string, you can define something like:

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
    """

    @classmethod
    def partial_validate(cls, name: str, value: Any) -> None:
        dict_formatter = DictFormatterValidator(name=name, value=value)
        _ = [parse(format_string) for format_string in dict_formatter.dict_with_format_strings]

    def __init__(self, name, value):
        DictFormatterValidator.__init__(self, name, value)
        Scriptable.__init__(self)

        self.unresolvable.add(VARIABLES.entry_metadata.variable_name)

    def initial_variables(
        self, unresolved_variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Returns
        -------
        Variables and format strings for all Override variables + additional variables (Optional)
        """
        initial_variables: Dict[str, str] = {}
        mergedeep.merge(
            initial_variables,
            self.dict_with_format_strings,
            unresolved_variables if unresolved_variables else {},
            {SUBSCRIPTION_NAME: self.subscription_name},
        )
        return ScriptUtils.add_sanitized_variables(initial_variables)

    def initialize_script(self, unresolved_variables: Set[str]) -> "Overrides":
        """
        Initialize the override script with override variables + any unresolved variables
        """
        self.script.add(
            self.initial_variables(
                unresolved_variables={
                    var_name: f"{{%throw('Plugin variable {var_name} has not been created yet')}}"
                    for var_name in unresolved_variables
                }
            )
        )
        self.unresolvable.update(unresolved_variables)
        self.update_script()
        return self

    @property
    def subscription_name(self) -> str:
        """
        Returns
        -------
        Name of the subscription
        """
        return self._root_name

    def apply_formatter(
        self,
        formatter: StringFormatterValidator,
        entry: Optional[Entry] = None,
        function_overrides: Dict[str, str] = None,
    ) -> str:
        """
        Parameters
        ----------
        formatter
            Formatter to apply
        entry
            Optional. Entry to add source variables to the formatter
        function_overrides
            Optional. Explicit values to override the overrides themselves and source variables

        Returns
        -------
        The format_string after .format has been called
        """
        script: Script = self.script
        unresolvable: Set[str] = self.unresolvable
        if entry:
            script = entry.script
            unresolvable = entry.unresolvable

        return formatter.post_process(
            str(
                script.resolve_once(
                    dict({"tmp_var": formatter.format_string}, **(function_overrides or {})),
                    unresolvable=unresolvable,
                )["tmp_var"]
            )
        )
