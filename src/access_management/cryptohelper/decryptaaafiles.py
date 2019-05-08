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
import os
import argparse
import json
import base64


class DecryptAAAFile(object):
    def __init__(self, pem_file):
        self.key = M2Crypto.RSA.load_key(pem_file)

    def decrypt_file(self, encrypted_file_path):
        with open(encrypted_file_path,'r') as encrypted_file:
            jsoned_file = json.load(encrypted_file)
            for user in jsoned_file["users"]:
                if len(user[1]) != 0:
                    decoded_pass = base64.b64decode(user[1])
                    decrypted_pass = self.key.private_decrypt(decoded_pass, M2Crypto.RSA.pkcs1_oaep_padding)
                    user[1] = decrypted_pass.decode('utf-32')
        return jsoned_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("key", help="Private key path")
    parser.add_argument("file", help="Path of the file to decrypt")
    args = parser.parse_args()
    dec = DecryptAAAFile(args.key)
    jsoned_file = dec.decrypt_file(args.file)
    if args.file.endswith(".enc"):
        decrypted_filename = args.file[:-4]
    else:
        decrypted_filename = args.file + ".dec"
    decrypted_file = open(os.path.join(decrypted_filename), 'w')
    decrypted_file.write(json.dumps(jsoned_file))
    decrypted_file.close()
    print "Decrypting file {0} for AAA done. New file name: {1}".format(args.file, decrypted_filename)
