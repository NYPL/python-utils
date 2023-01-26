# PythonUtils

This package contains common Python utility classes and functions.

## Classes
* Pushing records to Kinesis
* Setting and retrieving a resource in S3
* Encoding and decoding records using a given Avro schema
* Connecting to and querying a MySQL database
* Connecting to and querying a PostgreSQL database
* Connecting to and querying Redshift

## Functions
* Reading a YAML config file and putting the contents in os.environ
* Decrypting a value using KMS
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