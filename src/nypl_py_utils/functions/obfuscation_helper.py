import bcrypt
import os

from nypl_py_utils.functions.log_helper import create_log

logger = create_log('obfuscation_helper')


def obfuscate(input):
    """
    This method obfuscates an input according to NYPL standards using bcrypt.
    For more information on the obfuscation method, see
    https://github.com/NYPL/BIC/blob/main/obfuscating-identifiers.md.

    The method returns a string and takes one input: `input` can be of any type
    but is converted to a string before being obfuscated. The obfuscation salt
    is read from the `BCRYPT_SALT` environment variable.
    """
    logger.debug('Obfuscating input \'{}\' with environment salt'.format(
        input))
    hash = bcrypt.hashpw(str(input).encode(),
                         os.environ['BCRYPT_SALT'].encode()).decode()
    return hash.split(os.environ['BCRYPT_SALT'])[-1]


def obfuscate_with_salt(input, salt):
    """
    This method is the same as `obfuscate` above but takes the obfuscation salt
    as a string input.
    """
    logger.debug('Obfuscating input \'{}\' with custom salt'.format(input))
    hash = bcrypt.hashpw(str(input).encode(), salt.encode()).decode()
    return hash.split(salt)[-1]
