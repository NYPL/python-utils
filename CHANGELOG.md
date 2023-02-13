# Changelog

## v0.0.4 - 2/13
- In PostgreSQLClient, allow reconnecting after `close_connection` has been called
- Updated README with deployment information

## v0.0.3 - 2/10

- Added GitHub Actions workflow for deploying to production
- Switched PostgreSQLClient to use connection pooling

## v0.0.2 - 2/6

- Added CODEOWNERS
- Added GitHub Actions workflows for running tests and deploying to QA
- Added tests for helper functions
- Updated Avro encoder to avoid dependency on pandas

## v0.0.1 - 1/26

Initial version. Includes the `avro_encoder`, `kinesis_client`, `mysql_client`, `postgresql_client`, `redshift_client`, and `s3_client` classes as well as the `config_helper`, `kms_helper`, `log_helper`, and `obfuscation_helper` functions.