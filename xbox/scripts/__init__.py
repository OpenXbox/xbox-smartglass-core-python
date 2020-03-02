import os
import logging

from enum import IntEnum
from appdirs import user_data_dir

DATA_DIR = user_data_dir('xbox', 'OpenXbox')
TOKENS_FILE = os.path.join(DATA_DIR, 'tokens.json')
CONSOLES_FILE = os.path.join(DATA_DIR, 'consoles.json')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

LOG_FMT = '[%(asctime)s] %(levelname)s: %(message)s'
LOG_LEVEL_DEBUG_INCL_PACKETS = logging.DEBUG - 1
logging.addLevelName(LOG_LEVEL_DEBUG_INCL_PACKETS, 'DEBUG_INCL_PACKETS')


class ExitCodes(IntEnum):
    """
    Common CLI exit codes
    """
    OK = 0
    ArgParsingError = 1
    AuthenticationError = 2
    DiscoveryError = 3
    ConsoleChoice = 4


class VerboseFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super(VerboseFormatter, self).__init__(*args, **kwargs)
        self._verbosefmt = self._fmt + '\n%(_msg)s'

    def formatMessage(self, record):
        if '_msg' in record.__dict__:
            return self._verbosefmt % record.__dict__
        return self._style.format(record)
