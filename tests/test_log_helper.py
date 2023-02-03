import logging
import os

from freezegun import freeze_time
from nypl_py_utils.functions.log_helper import create_log


class TestLogHelper:

    @freeze_time('2023-01-01')
    def test_default_logging(self, caplog):
        logger = create_log('test_log')
        assert logger.getEffectiveLevel() == logging.INFO
        assert len(logger.handlers) == 1

        logger.info('Test info message')
        assert len(caplog.records) == 1
        assert logger.handlers[0].format(caplog.records[0]) == \
            '2022-12-31 19:00:00,000 | test_log | INFO: Test info message'

    @freeze_time('2023-01-01')
    def test_logging_with_custom_log_level(self, caplog):
        os.environ['LOG_LEVEL'] = 'error'
        logger = create_log('test_log')
        assert logger.getEffectiveLevel() == logging.ERROR

        logger.info('Test info message')
        logger.error('Test error message')
        assert len(caplog.records) == 1
        assert logger.handlers[0].format(caplog.records[0]) == \
            '2022-12-31 19:00:00,000 | test_log | ERROR: Test error message'
        del os.environ['LOG_LEVEL']

    @freeze_time('2023-01-01')
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
        assert logger.handlers[0].format(caplog.records[0]) == \
            '2022-12-31 19:00:00,000 | test_log | INFO: Test info message'
        assert logger.handlers[0].format(caplog.records[1]) == \
            '2022-12-31 19:00:00,000 | test_log | ERROR: Test error message'
        del os.environ['LOG_LEVEL']
