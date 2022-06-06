import argparse

###################################################################################################
# GLOBAL PARSER
from ytdl_sub.utils.logger import LoggerLevels

parser = argparse.ArgumentParser(
    description="ytdl-sub: Automate download and adding metadata with YoutubeDL"
)
parser.add_argument(
    "-c",
    "--config",
    metavar="CONFIGPATH",
    type=str,
    help="path to the config yaml, uses config.yaml if not provided",
    default="config.yaml",
)
parser.add_argument(
    "--log-level",
    metavar="|".join(LoggerLevels.names()),
    type=str,
    help="level of logs to print to console, defaults to info",
    default=LoggerLevels.name_of(LoggerLevels.INFO),
    choices=LoggerLevels.names(),
)
###################################################################################################
# SUBSCRIPTION PARSER
subparsers = parser.add_subparsers(dest="subparser")
subscription_parser = subparsers.add_parser("sub")
subscription_parser.add_argument(
    "subscription_paths",
    metavar="SUBPATH",
    nargs="*",
    help="path to subscription files, uses subscriptions.yaml if not provided",
    default=["subscriptions.yaml"],
)
###################################################################################################
# DOWNLOAD PARSER
download_parser = subparsers.add_parser("dl")
