from mnemonic import Mnemonic
from ecdsa import SigningKey, SECP256k1
import hashlib

class Wallet:
    @staticmethod
    def create():
        mnemo = Mnemonic('english')
        seed = mnemo.generate(strength=128)    # 12 palavras
        priv = SigningKey.generate(curve=SECP256k1)
        pub = priv.get_verifying_key()
        address = hashlib.sha256(pub.to_string()).hexdigest()[:40]
        w = Wallet()
        w.mnemonic = seed
        w.private_key_hex = priv.to_string().hex()
        w.public_key_hex = pub.to_string().hex()
        w.address = address
        return w

    @staticmethod
    def sign(payload: dict, priv_hex: str) -> str:
        sk = SigningKey.from_string(bytes.fromhex(priv_hex), curve=SECP256k1)
        msg = str(payload).encode()
        return sk.sign(msg).hex()
