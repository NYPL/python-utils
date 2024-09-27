import pytest

from nypl_py_utils.classes.sftp_client import SftpClient, SftpClientError

_TEST_PUBLIC_KEY = (
    'AAAAB3NzaC1yc2EAAAADAQABAAAAgQCHc5r1z7bCxJ+dwR4r65CKB4KBF6mB+VZNYPc/1kmyT'
    'vRh+P89asNvGDwATw7FZkz+g/0Z/Arak2ae454AHW7gBRO+TJ6YoAIrH2H5O3vQ4GGOepcTz3'
    '0ckuLoXtoaRMYzDTM1juvnITFq9fE5RMeFIM+Qc7BhOub/nDPLQI7/sw=='
)

_TEST_PRIVATE_KEY = (
    '-----BEGIN RSA PRIVATE KEY-----\nMIICWwIBAAKBgQCItzqS6yQYBq+923wf4pQ6M2u0'
    'pNMknrO4itBBQiDO6uDktZn2\nONnF1L9bYCtsucBGmRes6gdn+qFGTFRa+mWBHBO5CtOhbxA'
    'bH9K4MWi9B6fF6Riw\nUkhOIsXHQFPtPg23kF+0MV953CrhZMMdWmYh4EVaRFfRmQchsjJkP0'
    'eqBQIDAQAB\nAoGAEC+ZOLGsGUgZYGHu5Rt/LxDNbJqjAM/lOTD+DOvWVIkMTSeO7c63Qau5a'
    'AkP\nuxSWxgTz/53JeK78jwUUa5z/jUbD+4D0NbfjmFOXGlnVxs/kbx4z4tPwwArN6gMS\n7T'
    'fuEDgx4RF4a5kl5hOwDV1RUUCJ2TBO9wbm533ca7TvcCECQQDy3pKOB1ae9HM/\nYgtR6z1k0'
    'd734ujmDXpViESfvJpm+fd/o0MEh193cO9qGFDWiOU23axF/n5fIaaf\nhHt/8C/dAkEAkBtw'
    'bdQGDN9eZKH4XX1pRvB2PzUmrpgzZl3Zst8svKPDjeD9nm0Z\n+pGFLcVCIFT8ddUH1LSbt96'
    'a4wn5/dPUSQJAUs2fmdzWo4skX8/FnEBfxifnpQwv\n639c3hx/iRZ8be97eoDnMHwXCFnwxn'
    'NT3FEAFRyux45k93o5nNlGYfA54QJAKIwP\n7lch/K082gPY5jVLUfKG0vIZmDaq/7qYboPtC'
    'obplxofQlxgWuhnGKHQIVjIUD9I\nnMjUp7+yxP8hoBHiQQJAZsNUg/q1JNCEoa4Gqb89yygr'
    'x2fFOC/6eNp0ruWMRr5P\n8x1L+ugdXeUfI5vH7qI9wU+A7oADke63JBEHavv0UQ==\n-----'
    'END RSA PRIVATE KEY-----'
)


class TestSftpClient:

    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch('paramiko.SSHClient.connect')
        mocker.patch('paramiko.SSHClient.open_sftp')
        return SftpClient('test_host', 'test_user')

    def test_add_host_key(self, test_instance):
        assert len(test_instance.ssh_client.get_host_keys().keys()) == 0

        test_instance.add_host_key('ssh-rsa', _TEST_PUBLIC_KEY)

        assert len(test_instance.ssh_client.get_host_keys().keys()) == 1
        assert test_instance.ssh_client.get_host_keys().lookup(
            'test_host') is not None

    def test_connect_password(self, test_instance):
        test_instance.password = 'test_password'

        test_instance.connect()

        test_instance.ssh_client.connect.assert_called_once_with(
            'test_host', username='test_user', password='test_password',
            pkey=None)
        test_instance.ssh_client.open_sftp.assert_called_once()
        assert test_instance.sftp_conn is not None

    def test_connect_pkey(self, test_instance, mocker):
        mock_rsa_key = mocker.MagicMock()
        mock_pkey_method = mocker.patch('paramiko.RSAKey.from_private_key',
                                        return_value=mock_rsa_key)
        test_instance.private_key_str = _TEST_PRIVATE_KEY

        test_instance.connect()

        assert mock_pkey_method.call_args[0][0].read() == _TEST_PRIVATE_KEY
        test_instance.ssh_client.connect.assert_called_once_with(
            'test_host', username='test_user', password=None,
            pkey=mock_rsa_key)
        test_instance.ssh_client.open_sftp.assert_called_once()
        assert test_instance.sftp_conn is not None

    def test_download(self, test_instance, mocker):
        test_instance.sftp_conn = mocker.MagicMock()

        test_instance.download('remote/path', 'local/path')

        test_instance.sftp_conn.get.assert_called_once_with(
            'remote/path', 'local/path')

    def test_download_error(self, test_instance, mocker):
        test_instance.ssh_client = mocker.MagicMock()
        test_instance.sftp_conn = mocker.MagicMock()
        test_instance.sftp_conn.get.side_effect = IOError('test error')

        with pytest.raises(SftpClientError):
            test_instance.download('remote/path', 'local/path')

        test_instance.sftp_conn.get.assert_called_once_with(
            'remote/path', 'local/path')
        test_instance.sftp_conn.close.assert_called_once()
        test_instance.ssh_client.close.assert_called_once()

    def test_close_connection(self, test_instance, mocker):
        test_instance.sftp_conn = mocker.MagicMock()
        test_instance.ssh_client = mocker.MagicMock()

        test_instance.close_connection()

        test_instance.sftp_conn.close.assert_called_once()
        test_instance.ssh_client.close.assert_called_once()
