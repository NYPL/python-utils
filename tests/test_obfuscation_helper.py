import os

from nypl_py_utils.functions.obfuscation_helper import (obfuscate,
                                                        obfuscate_with_salt)

_TEST_SALT_1 = '$2a$10$8AvAPrrUsmlBa50qgc683e'
_TEST_SALT_2 = '$2b$12$iuSSdD6F/nJ1GSXzesM8sO'


class TestObfuscationHelper:

    def test_obfuscation_with_environment_variable(self):
        os.environ['BCRYPT_SALT'] = _TEST_SALT_1
        assert obfuscate('test_input') == 'UPMawmdZfleeSg5REsZbLbAivWl97O6'
        del os.environ['BCRYPT_SALT']

    def test_obfuscation_with_custom_salt(self):
        assert (obfuscate_with_salt('test_input', _TEST_SALT_2) ==
                'SUXLCHnsRVt4Vj1PyP9KPEqADxtUj5.')
