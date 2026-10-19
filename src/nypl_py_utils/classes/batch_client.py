import boto3
import os

from botocore.exceptions import ClientError
from nypl_py_utils.functions.log_helper import create_log


class BatchClient:
    """Client for interacting with AWS Batch"""

    def __init__(self):
        self.logger = create_log("batch_client")

        try:
            self.batch_client = boto3.client(
                "batch", region_name=os.environ.get("AWS_REGION", "us-east-1")
            )
        except ClientError as e:
            self.logger.error(
                "Could not create Batch client: {err}".format(err=e)
            )
            raise BatchClientError(
                "Could not create Batch client: {err}".format(err=e)
            ) from None

    def close(self):
        self.batch_client.close()

    def submit_job(
        self, job_name, job_definition, queue_name=None, env_vars={}
    ):
        """
        Submits a job to be run by AWS Batch.

        Parameters
        ----------
        job_name: str
            The name of the job. This is the developer's choice and is NOT the
            same as the job_definition, which must correspond to a known value.
        job_definition: str
            Name of the existing, registered job definition in AWS to run
        queue_name: str, optional
            Name of the job queue to use. If None, defaults to the
            job_definition string.
        env_vars: dict, optional
            Environment variables to use when running the job
        """
        formatted_env = [{"name": k, "value": v} for k, v in env_vars.items()]
        if queue_name is None:
            queue_name = job_definition

        self.logger.info(f"Submitting {job_definition} as {job_name}")
        try:
            if formatted_env:
                self.batch_client.submit_job(
                    jobName=job_name,
                    jobQueue=queue_name,
                    jobDefinition=job_definition,
                    containerOverrides={"environment": formatted_env},
                )
            else:
                self.batch_client.submit_job(
                    jobName=job_name,
                    jobQueue=queue_name,
                    jobDefinition=job_definition,
                )
        except ClientError as e:
            self.logger.error(f"Could not run {job_definition} job: {str(e)}")
            raise BatchClientError(
                f"Could not run {job_definition} job: {str(e)}"
            ) from None


class BatchClientError(Exception):
    def __init__(self, message=None):
        self.message = message
