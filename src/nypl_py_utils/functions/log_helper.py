import logging
import os
import structlog
import sys

levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


def get_structlog(module):
    """
    Standard logging without additional bindings looks as follows:
    {
        "level": "info",
        "timestamp": "2026-01-01T12:00:00.613719Z",
        "logger": "module param",
        "message": "this is a test log event"
    }

    Note that: 1) you should *NOT* use the same module name for a structlog
    and for a standard logger, and 2) using bind_contextvars will bind
    variables to *all* loggers. To bind a context variable on one logger
    without binding it to others, use `logger = logger.bind(contextvar=0)`.
    """
    logger = logging.getLogger(module)
    logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO').upper())

    # We assume existing loggers will handle logging to stdout and that we
    # don't need to do anything. Otherwise, manually add a stdout handler.
    if not logger.hasHandlers():
        logger.propagate = False
        logger.addHandler(logging.StreamHandler(sys.stdout))

    return structlog.wrap_logger(
        logger,
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.stdlib.add_logger_name,
            structlog.processors.EventRenamer('message'),
            structlog.processors.JSONRenderer(),
        ]
    )


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
    if json:
        return get_structlog(module)
    else:
        return standard_logger(module)
