import logging
import os
import time

from freezegun import freeze_time
from nypl_py_utils.functions.log_helper import create_log


@freeze_time('2023-01-01 19:00:00')
class TestLogHelper:

    def test_default_logging(self, caplog):
        logger = create_log('test_log')
        assert logger.getEffectiveLevel() == logging.INFO
        assert len(logger.handlers) == 1

        logger.info('Test info message')
        # freeze_time changes the utc time, while the logger uses local time by
        # default, so force the logger to use utc time
        logger.handlers[0].formatter.converter = time.gmtime
        assert len(caplog.records) == 1
        assert logger.handlers[0].format(caplog.records[0]) == \
            '2023-01-01 19:00:00,000 | test_log | INFO: Test info message'

    def test_logging_with_custom_log_level(self, caplog):
        os.environ['LOG_LEVEL'] = 'error'
        logger = create_log('test_log')
        assert logger.getEffectiveLevel() == logging.ERROR

        logger.info('Test info message')
        logger.error('Test error message')
        assert len(caplog.records) == 1
        # freeze_time changes the utc time, while the logger uses local time by
        # default, so force the logger to use utc time
        logger.handlers[0].formatter.converter = time.gmtime
        assert logger.handlers[0].format(caplog.records[0]) == \
            '2023-01-01 19:00:00,000 | test_log | ERROR: Test error message'
        del os.environ['LOG_LEVEL']

    def test_logging_no_duplicates(self, caplog):
        logger = create_log('test_log')
        logger.info('Test info message')

        # Test that logger uses the most recently set log level and doesn't
        # duplicate handlers/messages when create_log is called more than once.
        os.environ['LOG_LEVEL'] = 'error'
        logger = create_log('test_log')
        assert logger.getEffectiveLevel() == logging.ERROR
        assert len(logger.handlers) == 1

        logger.info('Test info message 2')
        logger.error('Test error message')
        assert len(caplog.records) == 2
        # freeze_time changes the utc time, while the logger uses local time by
        # default, so force the logger to use utc time
        logger.handlers[0].formatter.converter = time.gmtime
        assert logger.handlers[0].format(caplog.records[0]) == \
            '2023-01-01 19:00:00,000 | test_log | INFO: Test info message'
        assert logger.handlers[0].format(caplog.records[1]) == \
            '2023-01-01 19:00:00,000 | test_log | ERROR: Test error message'
        del os.environ['LOG_LEVEL']
