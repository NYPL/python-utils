import avro.schema
import requests

from avro.errors import AvroException
from avro.io import BinaryDecoder, BinaryEncoder, DatumReader, DatumWriter
from io import BytesIO
from nypl_py_utils.functions.log_helper import create_log
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import JSONDecodeError


class AvroClient:
    """
    Base class for Avro schema interaction. Takes as input the
    Platform API endpoint from which to fetch the schema in JSON format.
    """

    def __init__(self, platform_schema_url):
        self.logger = create_log("avro_client")
        retry_policy = Retry(total=3, backoff_factor=45,
                             status_forcelist=[500, 502, 503, 504],
                             allowed_methods=frozenset(['GET']))
        self.session = requests.Session()
        self.session.mount("https://",
                           HTTPAdapter(max_retries=retry_policy))
        self.schema = avro.schema.parse(
            self.get_json_schema(platform_schema_url))

    def get_json_schema(self, platform_schema_url):
        """
        Fetches a JSON response from the input Platform API endpoint and
        interprets it as an Avro schema.
        """
        self.logger.info(
            "Fetching Avro schema from {}".format(platform_schema_url))
        try:

            response = self.session.get(url=platform_schema_url,
                                        timeout=60)
            response.raise_for_status()
        except Exception as e:
            self.logger.error(
                "Failed to retrieve schema from {url}: {error}".format(
                    url=platform_schema_url, error=e
                )
            )
            raise AvroClientError(
                "Failed to retrieve schema from {url}: {error}".format(
                    url=platform_schema_url, error=e
                )
            )

        try:
            json_response = response.json()
            return json_response["data"]["schema"]
        except (JSONDecodeError, KeyError) as e:
            self.logger.error(
                "Retrieved schema is malformed: {errorType} {errorMessage}"
                .format(errorType=type(e), errorMessage=e)
            )
            raise AvroClientError(
                "Retrieved schema is malformed: {errorType} {errorMessage}"
                .format(errorType=type(e), errorMessage=e)
            ) from None


class AvroEncoder(AvroClient):
    """
    Class for encoding records using an Avro schema. Takes as input the
    Platform API endpoint from which to fetch the schema in JSON format.
    """

    def encode_record(self, record):
        """
        Encodes a single JSON record using the given Avro schema.

        Returns the encoded record as a byte string.
        """
        self.logger.debug(
            "Encoding record using {schema} schema".format(
                schema=self.schema.name)
        )
        datum_writer = DatumWriter(self.schema)
        with BytesIO() as output_stream:
            encoder = BinaryEncoder(output_stream)
            try:
                datum_writer.write(record, encoder)
                return output_stream.getvalue()
            except AvroException as e:
                self.logger.error("Failed to encode record: {}".format(e))
                raise AvroClientError(
                    "Failed to encode record: {}".format(e)) from None

    def encode_batch(self, record_list):
        """
        Encodes a list of JSON records using the given Avro schema.

        Returns a list of byte strings where each string is an encoded record.
        """
        self.logger.info(
            "Encoding ({num_rec}) records using {schema} schema".format(
                num_rec=len(record_list), schema=self.schema.name
            )
        )
        encoded_records = []
        datum_writer = DatumWriter(self.schema)
        with BytesIO() as output_stream:
            encoder = BinaryEncoder(output_stream)
            for record in record_list:
                try:
                    datum_writer.write(record, encoder)
                    encoded_records.append(output_stream.getvalue())
                    output_stream.seek(0)
                    output_stream.truncate(0)
                except AvroException as e:
                    self.logger.error("Failed to encode record: {}".format(e))
                    raise AvroClientError(
                        "Failed to encode record: {}".format(e)
                    ) from None
        return encoded_records


class AvroDecoder(AvroClient):
    """
    Class for decoding records using an Avro schema. Takes as input the
    Platform API endpoint from which to fetch the schema in JSON format.
    """

    def decode_record(self, record):
        """
        Decodes a single record represented using the given Avro
        schema. Input must be a bytes-like object.

        Returns a dictionary where each key is a field in the schema.
        """
        self.logger.debug(
            "Decoding {rec} using {schema} schema".format(
                rec=record, schema=self.schema.name
            )
        )
        datum_reader = DatumReader(self.schema)
        with BytesIO(record) as input_stream:
            decoder = BinaryDecoder(input_stream)
            try:
                return datum_reader.read(decoder)
            except Exception as e:
                self.logger.error("Failed to decode record: {}".format(e))
                raise AvroClientError(
                    "Failed to decode record: {}".format(e)) from None

    def decode_batch(self, record_list):
        """
        Decodes a list of JSON records using the given Avro schema. Input
        must be a list of bytes-like objects.

        Returns a list of strings where each string is a decoded record.
        """
        self.logger.info(
            "Decoding ({num_rec}) records using {schema} schema".format(
                num_rec=len(record_list), schema=self.schema.name
            )
        )
        decoded_records = []
        for record in record_list:
            decoded_record = self.decode_record(record)
            decoded_records.append(decoded_record)
        return decoded_records


class AvroClientError(Exception):
    def __init__(self, message=None):
        self.message = message
