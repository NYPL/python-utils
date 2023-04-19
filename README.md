# PythonUtils

This package contains common Python utility classes and functions.

## Classes
* Pushing records to Kinesis
* Setting and retrieving a resource in S3
* Decrypting values with KMS
* Encoding and decoding records using a given Avro schema
* Connecting to and querying a MySQL database
* Connecting to and querying a PostgreSQL database
* Connecting to and querying a PostgreSQL database using a connection pool
* Connecting to and querying Redshift
* Making requests to the Oauth2 authenticated APIs such as NYPL Platform API and Sierra

## Functions
* Reading a YAML config file and putting the contents in os.environ
* Creating a logger in the appropriate format
* Obfuscating a value using bcrypt

## Usage
```python
# test_file.py
from nypl_py_utils.classes.kinesis_client import KinesisClient
from nypl_py_utils.functions.config_helper import load_env_file

load_env_file(...)
kinesis_client = KinesisClient(...)
```

```bash
# requirements.txt
nypl-py-utils[kinesis-client,config-helper]==1.0.1

# Do not use any version below 1.0.0. All available optional dependencies can be found in pyproject.toml (see the "Managing dependencies" section below for more details).
```

## Developing locally
In order to use the local version of the package instead of the global version, use a virtual environment. To set up a virtual environment and install all the necessary dependencies, run:

```
python3 -m venv testenv
source testenv/bin/activate
pip install --upgrade pip
pip install .
pip install '.[development]'
deactivate && source testenv/bin/activate
```

## Managing dependencies
In order to prevent dependency bloat, this package has no required dependencies. Instead, each class and helper file has its own optional dependency set. For instance, if an app needs to use the KMS client and the obfuscation helper, it should add `nypl-py-utils[kms-client, obfuscation-helper]` to the app's requirements. This way, only the required dependencies are installed.

When a new client or helper file is created, a new optional dependency set should be added to `pyproject.toml`. The `development` dependency set, which includes all the dependencies required by all of the classes and tests, should also be updated.

The optional dependency sets also give the developer the option to manually list out the dependencies of the clients rather than relying upon what the package thinks is required, which can be beneficial in certain circumstances. For instance, AWS lambda functions come with `boto3` and `botocore` pre-installed, so it's not necessary to include these (rather hefty) dependencies in the lambda deployment package.

### Troubleshooting
If running `main.py` in this virtual environment produces the following error:
```
ImportError: no pq wrapper available.
Attempts made:
- couldn't import psycopg 'c' implementation: No module named 'psycopg_c'
- couldn't import psycopg 'binary' implementation: No module named 'psycopg_binary'
- couldn't import psycopg 'python' implementation: dlsym(0x7f8620446f40, PQsslInUse): symbol not found
```

then try running:
```
pip uninstall psycopg
pip install "psycopg[c]"
```

## Git workflow
This repo uses the [Main-QA-Production](https://github.com/NYPL/engineering-general/blob/main/standards/git-workflow.md#main-qa-production) git workflow.

[`main`](https://github.com/NYPL/python-utils/tree/main) has the latest and greatest commits, [`qa`](https://github.com/NYPL/python-utils/tree/qa) has what's in our QA environment, and [`production`](https://github.com/NYPL/python-utils/tree/production) has what's in our production environment.

### Ideal Workflow
- Cut a feature branch off of `main`
- Commit changes to your feature branch
- File a pull request against `main` and assign a reviewer (who must be an owner)
  - In order for the PR to be accepted, it must pass all unit tests, have no lint issues, and update the CHANGELOG (or contain the `Skip-Changelog` label in GitHub)
- After the PR is accepted, merge into `main`
- Merge `main` > `qa`
- Deploy app to QA on GitHub and confirm it works
- Merge `qa` > `production`
- Deploy app to production on GitHub and confirm it works

## Deployment
The utils repo is deployed as a PyPI package [here](https://pypi.org/project/nypl-py-utils/) and as a Test PyPI package for QA purposes [here](https://test.pypi.org/project/nypl-py-utils/). In order to be deployed, the version listed in `pyproject.toml` **must be updated**. To deploy to Test PyPI, create a new release in GitHub and tag it `qa-vX.X.X`. The GitHub Actions deploy-qa workflow will then build and publish the package. To deploy to production PyPI, create a release and tag it `production-vX.X.X`.
