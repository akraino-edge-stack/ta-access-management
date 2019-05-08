# Copyright 2019 Nokia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import M2Crypto
import argparse
import json
import base64


class EncryptAAAFile(object):
    def __init__(self, pem_file):
        self.key = M2Crypto.RSA.load_pub_key(pem_file)


    def encrypt_file(self, file_path):
        with open(file_path,'r') as file:
            jsoned_file = json.load(file)
            for user in jsoned_file["users"]:
                encrypted_pass = self.key.public_encrypt(user[1], M2Crypto.RSA.pkcs1_oaep_padding)
                encoded_pass = base64.b64encode(encrypted_pass)
                user[1] = encoded_pass
            encrypted_file_name = file_path + ".enc"
            with open(encrypted_file_name, 'w') as encrypted_file:
                encrypted_file.write(json.dumps(jsoned_file))
        return encrypted_file_name


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("key", help="Public key path")
    parser.add_argument("file", help="Path of the file to encrypt")
    args = parser.parse_args()
    enc = EncryptAAAFile(args.key)
    encrypted_file_name = enc.encrypt_file(args.file)
    print "Encrypting file {0} for AAA done. New file name: {1}".format(args.file, encrypted_file_name)
