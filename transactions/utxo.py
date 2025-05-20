import json
import os
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
import hashlib
from ecdsa.util import sigdecode_der
class UTXO:
    def __init__(self, txid: str, index: int, address: str, amount: float, public_key: str):
        self.txid = txid
        self.index = index
        self.address = address
        self.amount = amount
        self.public_key = public_key  # Era locking_script

    def to_dict(self):
        return {
            "txid": self.txid,
            "index": self.index,
            "address": self.address,
            "amount": self.amount,
            "public_key": self.public_key
        }

class UTXOSet:
    def __init__(self):
        self.utxos = {}

        # Caminho absoluto para o arquivo data/utxos.json baseado neste arquivo
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # sobe de transactions/ para server/
        self.utxos_file = os.path.join(base_dir, 'data', 'utxos.json')

    def add_utxo(self, address, txid, index, amount, public_key):
        if txid not in self.utxos:
            self.utxos[txid] = {}
        self.utxos[txid][index] = UTXO(txid, index, address, amount, public_key)

    def spend_utxo(self, txid, index):
        if txid in self.utxos and index in self.utxos[txid]:
            del self.utxos[txid][index]
            if not self.utxos[txid]:
                del self.utxos[txid]

    def get_utxo(self, txid, index):
        return self.utxos.get(txid, {}).get(index)

    def save_utxos(self):
        os.makedirs(os.path.dirname(self.utxos_file), exist_ok=True)
        with open(self.utxos_file, 'w') as f:
            serializable = {
                txid: {str(idx): utxo.to_dict() for idx, utxo in indexes.items()}
                for txid, indexes in self.utxos.items()
            }
            json.dump(serializable, f, indent=2)

    def load_utxos(self):
        try:
            with open(self.utxos_file, 'r') as f:
                data = json.load(f)
                self.utxos = {}
                for txid, indexes in data.items():
                    self.utxos[txid] = {}
                    for idx_str, utxo_dict in indexes.items():
                        idx = int(idx_str)
                        utxo = UTXO(
                            txid=utxo_dict['txid'],
                            index=idx,
                            address=utxo_dict['address'],
                            amount=utxo_dict['amount'],
                            public_key=utxo_dict['public_key']
                        )
                        self.utxos[txid][idx] = utxo
                print(f"[DEBUG] UTXOs carregados: {len(self.utxos)} txids, total {sum(len(v) for v in self.utxos.values())} UTXOs")
        except FileNotFoundError:
            self.utxos = {}
            print(f"[DEBUG] Arquivo {self.utxos_file} não encontrado, iniciando vazio")

    def get_balance(self, address):
        return sum(
            utxo.amount
            for txs in self.utxos.values()
            for utxo in txs.values()
            if utxo.address == address
        )

    def find_utxos(self, address):
        return [
            utxo
            for txs in self.utxos.values()
            for utxo in txs.values()
            if utxo.address == address
        ]

# Assinatura
def verify_signature(public_key_hex, msg, signature_hex):
    try:
        pub_key_bytes = bytes.fromhex(public_key_hex)
        signature_bytes = bytes.fromhex(signature_hex)
        vk = VerifyingKey.from_string(pub_key_bytes, curve=SECP256k1)
        msg_hash = hashlib.sha256(msg.encode()).digest()
        return vk.verify(signature_bytes, msg_hash, sigdecode=sigdecode_der, prehashed=True)
    except (BadSignatureError, Exception):
        return False
# Verificação de transação
def is_valid_transaction(tx, utxo_set):
    # Exemplo simples do que pode ter na validação
    for i, inp in enumerate(tx['inputs']):
        public_key_hex = inp['public_key']
        signature_hex = inp.get('signature')

        # Dados que deveriam ser verificados (exemplo baseado no seu sign_digest)
        signing_data = f"{tx['txid']}:{i}".encode()
        hashed_data = hashlib.sha256(signing_data).digest()

        print(f"[DEBUG VALIDATION] Input {i}")
        print(f"  Public Key: {public_key_hex}")
        print(f"  Signature: {signature_hex}")
        print(f"  Signing data (string): {signing_data}")
        print(f"  Signing data (sha256 hex): {hashed_data.hex()}")

        # Aqui você deve colocar o código que usa a biblioteca ecdsa pra verificar:
        try:
            verifying_key = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
            # Verifica assinatura, usando verify_digest
            verifying_key.verify_digest(bytes.fromhex(signature_hex), hashed_data)
        except BadSignatureError:
            print(f"[DEBUG VALIDATION] Assinatura inválida para input {i}")
            return False, f"Assinatura inválida para input {i}"

    # Continua validação dos outros aspectos da transação...
    return True, "Transação válida"