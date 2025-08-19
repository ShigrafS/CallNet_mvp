# identity.py

import hashlib
from ecdsa import SigningKey, Ed25519
import os

KEY_PATH = "device_key.pem"

def get_device_id_and_key():
    # Load or generate a new private key
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, 'rb') as f:
            sk = SigningKey.from_pem(f.read())
    else:
        sk = SigningKey.generate(curve=Ed25519)
        with open(KEY_PATH, 'wb') as f:
            f.write(sk.to_pem(format="pkcs8"))

    vk = sk.verifying_key
    public_key_bytes = vk.to_string()

    # Create a device ID by hashing the public key
    device_id = hashlib.sha256(public_key_bytes).hexdigest()[:20]

    # Export public key as PEM
    public_key_pem = vk.to_pem().decode()

    return device_id, public_key_pem
