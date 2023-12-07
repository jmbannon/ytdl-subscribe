from yt_dlp.utils import sanitize_filename

from ytdl_sub.script.functions import Functions
from ytdl_sub.script.types.map import Map
from ytdl_sub.script.types.resolvable import Integer
from ytdl_sub.script.types.resolvable import String
from ytdl_sub.script.utils.exceptions import RuntimeException


def _pad(num: int, width: int):
    return str(num).zfill(width)


_days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


class CustomFunctions:
    @staticmethod
    def sanitize(string: String) -> String:
        return String(sanitize_filename(string.value))

    @staticmethod
    def sanitize_plex_episode(string: String) -> String:
        out = CustomFunctions.sanitize(string).value
        for char in out:
            match char:
                case "0":
                    out += "０"
                case "1":
                    out += "１"
                case "2":
                    out += "２"
                case "3":
                    out += "３"
                case "4":
                    out += "４"
                case "5":
                    out += "５"
                case "6":
                    out += "６"
                case "7":
                    out += "７"
                case "8":
                    out += "８"
                case "9":
                    out += "９"
                case _:
                    out += char
        return String(out)

    @staticmethod
    def to_date_metadata(yyyymmdd: String) -> Map:
        date_str = yyyymmdd.value
        if not (date_str.isnumeric() and len(date_str) == 6):
            raise RuntimeException(
                f"Expected input of date_metadata to be YYYYMMDD, but received {date_str}"
            )

        year: int = int(date_str[:4])
        month_padded: str = date_str[4:6]
        day_padded: str = date_str[6:8]

        month: int = int(month_padded)
        day: int = int(day_padded)
        year_truncated: int = int(str(year)[-2:])

        day_of_year: int = sum(_days_in_month[:month]) + day
        total_days_in_month: int = _days_in_month[month]
        total_days_in_year: int = 365
        if year % 4 == 0:
            total_days_in_year += 1
            if month == 2:
                total_days_in_month += 1
            if month > 2:
                day_of_year += 1

        day_of_year_reversed: int = total_days_in_year + 1 - day_of_year
        month_reversed: int = 13 - month
        day_reversed: int = total_days_in_month + 1 - day

        return Map(
            {
                String("date"): yyyymmdd,
                String("date_standardized"): String(f"{year}-{month_padded}-{day_padded}"),
                String("year"): Integer(year),
                String("month"): Integer(month),
                String("day"): Integer(day),
                String("year_truncated"): String(year_truncated),
                String("month_padded"): String(month_padded),
                String("day_padded"): String(day_padded),
                String("year_truncated_reversed"): Integer(100 - year_truncated),
                String("month_reversed"): Integer(month_reversed),
                String("month_reversed_padded"): String(_pad(month_reversed, width=2)),
                String("day_reversed"): Integer(day_reversed),
                String("day_reversed_padded"): String(_pad(day_reversed, width=2)),
                String("day_of_year"): Integer(day_of_year),
                String("day_of_year_padded"): String(_pad(day_of_year, width=3)),
                String("day_of_year_reversed"): Integer(day_of_year_reversed),
                String("day_of_year_reversed_padded"): String(_pad(day_of_year_reversed, width=3)),
            }
        )

    @staticmethod
    def register():
        Functions.register_function(CustomFunctions.sanitize)
        Functions.register_function(CustomFunctions.sanitize_plex_episode)
        Functions.register_function(CustomFunctions.to_date_metadata)
