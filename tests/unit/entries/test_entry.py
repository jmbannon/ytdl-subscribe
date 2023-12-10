from typing import Callable

import pytest

from ytdl_sub.config.overrides import Overrides
from ytdl_sub.entries.entry import Entry
from ytdl_sub.entries.script.variable_definitions import VARIABLES as v
from ytdl_sub.entries.script.variable_scripts import ENTRY_INJECTED_VARIABLES
from ytdl_sub.entries.script.variable_scripts import ENTRY_RELATIVE_VARIABLES
from ytdl_sub.entries.script.variable_scripts import UNRESOLVED_VARIABLES


@pytest.fixture
def mock_overrides_factory() -> Callable[[Entry], Overrides]:
    def _mock_overrides_factory(entry: Entry) -> Overrides:
        overrides = Overrides(name="test", value={})
        overrides.initialize_script(unresolved_variables=set())

        overrides.add(
            {
                var.variable_name: format_string
                for var, format_string in (
                    list(ENTRY_INJECTED_VARIABLES.items()) + list(ENTRY_RELATIVE_VARIABLES.items())
                )
            }
        )

        overrides.add_entry_kwargs(entry._kwargs)
        return overrides

    return _mock_overrides_factory


class TestEntry(object):
    def test_entry_to_dict(self, mock_overrides_factory, mock_entry, mock_entry_to_dict):
        out = mock_overrides_factory(mock_entry).to_dict()
        assert out == mock_entry_to_dict

    def test_entry_missing_kwarg(self, mock_entry):
        key = "dne"
        expected_error_msg = f"Expected '{key}' in Entry but does not exist."

        assert mock_entry.kwargs_contains(key) is False
        with pytest.raises(KeyError, match=expected_error_msg):
            mock_entry.kwargs(key)

    @pytest.mark.parametrize(
        "upload_date, year_rev, month_rev, day_rev, month_rev_pad, day_rev_pad",
        [
            ("20000228", 100, 11, 2, "11", "02"),
            ("20200808", 80, 5, 24, "05", "24"),
        ],
    )
    def test_entry_reverse_variables(
        self,
        mock_overrides_factory,
        mock_entry_kwargs,
        upload_date,
        year_rev,
        month_rev,
        day_rev,
        month_rev_pad,
        day_rev_pad,
    ):
        mock_entry_kwargs["upload_date"] = upload_date
        overrides = mock_overrides_factory(
            Entry(entry_dict=mock_entry_kwargs, working_directory=".")
        )

        assert overrides.get_int(v.upload_year_truncated_reversed) == year_rev
        assert overrides.get_int(v.upload_month_reversed) == month_rev
        assert overrides.get_int(v.upload_day_reversed) == day_rev
        assert overrides.get_str(v.upload_month_reversed_padded) == month_rev_pad
        assert overrides.get_str(v.upload_day_reversed_padded) == day_rev_pad

    @pytest.mark.parametrize(
        "upload_date, day_year, day_year_rev, day_year_pad, day_year_rev_pad",
        [
            ("20000228", 59, 308, "059", "308"),
            ("20210808", 220, 146, "220", "146"),
        ],
    )
    def test_entry_upload_day_of_year_variables(
        self,
        mock_overrides_factory,
        mock_entry_kwargs,
        upload_date,
        day_year,
        day_year_rev,
        day_year_pad,
        day_year_rev_pad,
    ):
        mock_entry_kwargs["upload_date"] = upload_date
        overrides = mock_overrides_factory(
            Entry(entry_dict=mock_entry_kwargs, working_directory=".")
        )

        assert overrides.get_int(v.upload_day_of_year) == day_year
        assert overrides.get_int(v.upload_day_of_year_reversed) == day_year_rev
        assert overrides.get_str(v.upload_day_of_year_padded) == day_year_pad
        assert overrides.get_str(v.upload_day_of_year_reversed_padded) == day_year_rev_pad
