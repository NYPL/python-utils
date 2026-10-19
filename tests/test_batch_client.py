import pytest

from botocore.exceptions import ClientError
from nypl_py_utils.classes.batch_client import BatchClient, BatchClientError


class TestBatchClient:

    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch('boto3.client')
        return BatchClient()

    def test_submit_job_defaults(self, test_instance):
        test_instance.submit_job("job_name", "job_def")
        test_instance.batch_client.submit_job.assert_called_once_with(
            jobName="job_name",
            jobQueue="job_def",
            jobDefinition="job_def"
        )

    def test_submit_job_overrides(self, test_instance):
        test_instance.submit_job(
            "job_name", "job_def",
            queue_name="queue_name",
            env_vars={"var1": "val1", "var2": 2}
        )
        test_instance.batch_client.submit_job.assert_called_once_with(
            jobName="job_name",
            jobQueue="queue_name",
            jobDefinition="job_def",
            containerOverrides={"environment": [
                {"name": "var1", "value": "val1"},
                {"name": "var2", "value": 2}
            ]}
        )

    def test_submit_job_error(self, test_instance):
        test_instance.batch_client.submit_job.side_effect = \
            ClientError({}, 'SubmitJob')
        with pytest.raises(BatchClientError):
            test_instance.submit_job("job_name", "job_def")
