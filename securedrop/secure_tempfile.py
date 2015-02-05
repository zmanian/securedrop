import base64
import os
from tempfile import _TemporaryFileWrapper

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

crypto_backend = default_backend()

class SecureTemporaryFile(_TemporaryFileWrapper):
    """Temporary file that is ephemerally encrypted on the fly.

    Since only encrypted data is ever written to disk, using this
    classes minimizes the chances of plaintext recovery through
    forensic disk analysis.

    Adapated from Globaleaks' GLSecureTemporaryFile: https://github.com/globaleaks/GlobaLeaks/blob/master/backend/globaleaks/security.py#L35

    WARNING: you can't use this like a normal file object. It supports
    being written to exactly once, then read from exactly once.
    """

    AES_key_size = 32
    AES_counter_nonce = 16 # AES block size

    def __init__(self, store_dir):
        self.last_action = 'init'
        self.create_key()

        self.tmp_file_id = base64.urlsafe_b64encode(os.urandom(32)).strip('=')
        self.filepath = os.path.join(store_dir, "{}.aes".format(self.tmp_file_id))
        self.file = open(self.filepath, 'w+b')

        _TemporaryFileWrapper.__init__(self, self.file, self.filepath, delete=True)

    def create_key(self):
        """
        Randomly generate an AES key to encrypt the file
        """
        self.key = os.urandom(self.AES_key_size)
        self.key_counter_nonce = os.urandom(self.AES_counter_nonce)
        self.initialize_cipher()

    def initialize_cipher(self):
        self.cipher = Cipher(algorithms.AES(self.key), modes.CTR(self.key_counter_nonce), backend=crypto_backend)
        self.encryptor = self.cipher.encryptor()
        self.decryptor = self.cipher.decryptor()

    def write(self, data):
        """
        We track the internal status and don't allow writing after reading.
        It might be possible to be smarter about this.
        """
        assert self.last_action != 'read', "You cannot write after read!"
        self.last_action = 'write'

        try:
            if isinstance(data, unicode):
                data = data.encode('utf-8')
            self.file.write(self.encryptor.update(data))
        except Exception as err:
            raise err

    def read(self, count=None):
        """
        The first time 'read' is called after a write, automatically seek(0).
        """
        if self.last_action == 'write':
            # Note: there is no need to finalize in CTR mode.
            self.seek(0, 0)
            self.last_action = 'read'

        if count is None:
            return self.decryptor.update(self.file.read())
        else:
            return self.decryptor.update(self.file.read(count))

    def close(self):
        return _TemporaryFileWrapper.close(self)

