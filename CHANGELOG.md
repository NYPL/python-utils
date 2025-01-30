# Changelog
## v1.6.4 1/30/25
- Update pyproject.toml to reflect CL changes (since omitted in last release)

## v1.6.3 1/27/25
- Add capability to pull cloudLibrary events by the millisecond

## v1.6.2 12/2/24
- Add record_num capability to patron_data_helper

## v1.6.1 11/26/24
- Accidental duplicate of v1.6.0

## v1.6.0 11/20/24
- Added patron_data_helper functions
- Use executemany instead of execute when appropriate in PostgreSQLClient
- Add capability to retry connecting to a database to the MySQL, PostgreSQL, and Redshift clients
- Automatically close database connection upon error in the MySQL, PostgreSQL, and Redshift clients
- Delete old PostgreSQLPoolClient, which was not production ready

## v1.5.0 11/19/24
- Added cloudLibrary client

## v1.4.0 9/23/24
- Added SFTP client

## v1.3.2 8/1/24
- Replaced info statements with debug for security purposes

## v1.3.1 7/31/24
- Replaced log statement in Avro client with debug

## v1.3.0 7/30/24
- Added SecretsManager client

## v1.2.1 7/25/24
- Add retry for fetching Avro schemas

## v1.2.0 7/17/24
- Generalized Avro functions and separated encoding/decoding behavior

## v1.1.6 7/12/24
- Add put functionality to Oauth2 Client
- Update pyproject version 

## v1.1.5 6/6/24
- Use executemany instead of execute when appropriate in RedshiftClient.execute_transaction

## v1.1.4 3/14/24
- Fix bug with oauth2 requests after token refresh

## v1.1.3 11/9/23
- Finalize retry logic in Oauth2 Client

## v1.1.2
- Update config_helper to accept list environment variables

## v1.1.0/v1.1.1
- Add retries for empty responses in Oauth2 Client. This was added to address a known quirk in the Sierra API where this response is returned:
```
> GET / HTTP/1.1
> Host: ilsstaff.nypl.org
> User-Agent: curl/7.64.1
> Accept: */*
>
```
- Due to an accidental deployment, v1.1.0 and v1.1.1 were both released but are identical

## v1.0.4 - 6/28/23
- Enforce Kinesis stream 1000 records/second write limit

## v1.0.3 - 5/19/23
- Add research_catalog_identifier_helper function

## v1.0.2 - 5/18/23
- Identical to v1.0.1 -- this was mistakenly deployed to QA without any changes

## v1.0.1 - 4/3/23
- Add transaction support to RedshiftClient

## v1.0.0 - 3/22/23
- Improve Oauth2ApiClient token refresh and method responses
- Create separate PostgreSQLClient and PostgreSQLPoolClient classes
- Update PostgreSQL and MySQL clients to accept write queries implicitly
- Update RedshiftClient to ensure SSL is being used
- Separate dependencies to slim down package installation

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
