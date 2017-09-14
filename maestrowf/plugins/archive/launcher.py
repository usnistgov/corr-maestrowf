
from argparse import ArgumentParser, RawTextHelpFormatter
import inspect
import logging
import os
import sys

from maestrowf.utils import create_parentdir
from director import Director
import utils

# Program Globals
ROOTLOGGER = logging.getLogger(inspect.getmodule(__name__))
LOGGER = logging.getLogger(__name__)

# Configuration globals
LFORMAT = "%(asctime)s - %(name)s:%(funcName)s:%(lineno)s - " \
          "%(levelname)s - %(message)s"
DEFAULT_ARCHIVE_CONFIG = 'configs/corrhttp-config.json'
def setup_argparser():
    """
    Method for setting up the program's argument parser.
    """
    parser = ArgumentParser(prog="ArchiveDirector",
                            description="The Archive Director for archiving "
                            "Maestro Workflow Conductor workflows.",
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("specification", type=str, help="The path to a Study"
                        " YAML specification that will drive the archiving.")
    parser.add_argument("-a", "--archiver", type=str, default='corrhttp',
                        help="Which archiver to use:\n"
                        "corrhttp - The CoRR HTTP Archiver (Default)")
    parser.add_argument("-f", "--config", type=str,
                        default=DEFAULT_ARCHIVE_CONFIG, help="Which config file"
                        " to use for the specified archiver. Defaults to:\n"
                        "maestrowf/plugins/archive/configs/"
                        "corrhttp-config.json")
    parser.add_argument("-l", "--logpath", type=str,
                        help="Alternate path to store program logging.")
    parser.add_argument("-d", "--debug_lvl", type=int, default=2,
                        help="Level of logging messages to be output:\n"
                             "5 - Critical\n"
                             "4 - Error\n"
                             "3 - Warning\n"
                             "2 - Info (Default)\n"
                             "1 - Debug")
    parser.add_argument("-c", "--logstdout", action="store_true",
                        help="Log to stdout in addition to a file.")
    return parser

def setup_logging(args, path, name):
    """
    Utility method to set up logging based on the ArgumentParser.

    :param args: A Namespace object created by a parsed ArgumentParser.
    :param path: A default path to be used if a log path is not specified by
    user command line arguments.
    :param name: The name of the log file.
    """
    # If the user has specified a path, use that.
    if args.logpath:
        logpath = args.logpath
    # Otherwise, we should just output to the OUTPUT_PATH.
    else:
        logpath = os.path.join(path, "logs")

    loglevel = args.debug_lvl * 10

    # Create the FileHandler and add it to the logger.
    create_parentdir(logpath)
    formatter = logging.Formatter(LFORMAT)
    ROOTLOGGER.setLevel(loglevel)

    logname = "{}.log".format(name)
    fh = logging.FileHandler(os.path.join(logpath, logname))
    fh.setLevel(loglevel)
    fh.setFormatter(formatter)
    ROOTLOGGER.addHandler(fh)

    if args.logstdout:
        # Add the StreamHandler
        sh = logging.StreamHandler()
        sh.setLevel(loglevel)
        sh.setFormatter(formatter)
        ROOTLOGGER.addHandler(sh)

    # Print the level of logging.
    LOGGER.info("INFO Logging Level -- Enabled")
    LOGGER.warning("WARNING Logging Level -- Enabled")
    LOGGER.critical("CRITICAL Logging Level -- Enabled")
    LOGGER.debug("DEBUG Logging Level -- Enabled")

def main():
    """
    The director main function.
    """
    parser = setup_argparser()
    args = parser.parse_args()
    default_log_path = os.path.dirname(os.path.abspath(__file__))
    setup_logging(args, default_log_path, 'lulesh')
    # Grab absolute file path of config if config file is default
    if args.config == DEFAULT_ARCHIVE_CONFIG:
        config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   args.config)
    else:
        config_path = args.config
    director = Director(adapter=args.archiver, config_path=config_path)
    director.archive(args.specification)
    sys.exit(0)

if __name__ == "__main__":
    main()
