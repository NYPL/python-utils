# PythonUtils

This package contains common Python utility classes and functions.

## Classes
* Pushing records to Kinesis
* Setting and retrieving a resource in S3
* Decrypting values with KMS
* Encoding and decoding records using a given Avro schema
* Connecting to and querying a MySQL database
* Connecting to and querying a PostgreSQL database using a connection pool
* Connecting to and querying Redshift

## Functions
* Reading a YAML config file and putting the contents in os.environ
* Creating a logger in the appropriate format
* Obfuscating a value using bcrypt

## Developing locally
In order to use the local version of the package instead of the global version, use a virtual environment. To set up a virtual environment and install all the necessary dependencies, run:

```bash
python3 -m venv testenv
source testenv/bin/activate
pip install --upgrade pip
pip install .
pip install '.[tests]'
deactivate && source testenv/bin/activate
```

Add any new dependencies required by code in the `nypl_py_utils` directory to the `dependencies` section of `pyproject.toml`. Add dependencies only required by code in the `tests` directory to the `[project.optional-dependencies]` section.

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