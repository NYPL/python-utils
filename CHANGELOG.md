# Changelog

## v0.0.9 - 5/18/23
- Add research_catalog_identifier_helper function

## v0.0.8 - 3/3/23
- Pass in all kwargs from PostgreSQLClient to ConnectionPool so that all ConnectionPool settings
can be set from the wrapper

## v0.0.7 - 3/1/23
- Added Oauth2ApiClient for oauth2 authenticated calls to our Platform API and Sierra
- Set PostgreSQL connection pool to have a default pool size minimum of 0

## v0.0.5 - 2/22/23
- Support write queries to PostgreSQL and MySQL databases
- Support different return formats when querying PostgreSQL, MySQL, and Redshift databases

## v0.0.4 - 2/13/23
- In PostgreSQLClient, allow reconnecting after `close_connection` has been called
- Updated README with deployment information

## v0.0.3 - 2/10/23
- Added GitHub Actions workflow for deploying to production
- Switched PostgreSQLClient to use connection pooling

## v0.0.2 - 2/6/23
- Added CODEOWNERS
- Added GitHub Actions workflows for running tests and deploying to QA
- Added tests for helper functions
- Updated Avro encoder to avoid dependency on pandas

## v0.0.1 - 1/26/23
Initial version. Includes the `avro_encoder`, `kinesis_client`, `mysql_client`, `postgresql_client`, `redshift_client`, and `s3_client` classes as well as the `config_helper`, `kms_helper`, `log_helper`, and `obfuscation_helper` functions.
