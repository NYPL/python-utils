import bcrypt
import os

from log_helper import create_log

logger = create_log('obfuscation_helper')


def obfuscate(input):
    logger.debug('Obfuscating input \'{}\''.format(input))
    hash = bcrypt.hashpw(str(input).encode(),
                         os.environ['BCRYPT_SALT'].encode())
    return hash[29:].decode()
