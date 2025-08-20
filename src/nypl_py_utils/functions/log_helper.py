import structlog

import logging
import os
import sys

levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


# Configure structlog to be machine-readable first and foremost
# while still making it easy for humans to parse
# End result (without additional bindings) is JSON like this:
#
# { "logger": "module param"
#   "message": "this is a test log event",
#  "level": "info",
#  "timestamp": "2023-11-01 18:50:47"}
#
def get_structlog(module):
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.EventRenamer("message"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    return structlog.get_logger(module)


def standard_logger(module):
    logger = logging.getLogger(module)
    if logger.hasHandlers():
        logger.handlers = []

    console_log = logging.StreamHandler(stream=sys.stdout)

    log_level = os.environ.get('LOG_LEVEL', 'info').lower()

    logger.setLevel(levels[log_level])
    console_log.setLevel(levels[log_level])

    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s: %(message)s')
    console_log.setFormatter(formatter)

    logger.addHandler(console_log)
    return logger


def create_log(module, json=False):
    if (json):
        return get_structlog(module)
    else:
        return standard_logger(module)
