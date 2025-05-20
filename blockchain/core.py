import hashlib
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from nodes.node_manager import NodeManager
from transactions.utxo import UTXOSet
from blockchain.consensus import ProofOfEnergy
from ecdsa import SigningKey, SECP256k1, VerifyingKey

def compress_pubkey(pubkey_hex: str) -> str:
    # Remove o prefixo 0x04 que indica chave pública não comprimida
    pubkey_bytes = bytes.fromhex(pubkey_hex)
    if pubkey_bytes[0] == 0x04:
        vk = VerifyingKey.from_string(pubkey_bytes[1:], curve=SECP256k1)
        compressed = vk.to_string("compressed").hex()
        return compressed
    else:
        # Já comprimida ou formato diferente, retorna original
        return pubkey_hex

# Geração da chave para endereço (exemplo, pode não ser usada diretamente aqui)
sk = SigningKey.generate(curve=SECP256k1)
vk = sk.verifying_key

# Chave pública não comprimida (com prefixo 04)
public_key_uncompressed = '04' + vk.to_string().hex()

# Chave pública comprimida (sem prefixo 04)
public_key_compressed = compress_pubkey(public_key_uncompressed)

# Hash SHA-1 da chave pública comprimida para gerar o endereço
address = hashlib.sha1(public_key_compressed.encode()).hexdigest()

_blockchain = None

def init_blockchain():
    global _blockchain
    if _blockchain is None:
        _blockchain = Blockchain()
    return _blockchain
def mine_mempool_transactions(blockchain, mempool, max_txs=100):
    pending_txs = mempool.get_transactions_for_block(max_txs)
    if not pending_txs:
        print("[MINER] Nenhuma transação pendente para minerar.")
        return None

    valid_txs = []
    for tx in pending_txs:
        if is_valid_transaction(tx, blockchain.utxo_set):
            valid_txs.append(tx)
        else:
            print(f"[MINER] Transação inválida descartada: {tx['txid']}")

    if not valid_txs:
        print("[MINER] Nenhuma transação válida após verificação.")
        return None

    daily_data = blockchain.node_manager.aggregate_daily_data()
    print("[DEBUG] daily_data:", daily_data)  # DEBUG

    if daily_data is None or 'total_energy' not in daily_data:
        print("[MINER] daily_data inválido para minerar bloco.")
        return None

    daily_data['transactions'] = valid_txs
    blockchain.node_manager.aggregate_daily_data = lambda: daily_data

    try:
        new_block = blockchain.add_block()
    except Exception as e:
        print(f"[ERROR] Falha ao minerar bloco: {e}")
        return None

    mempool.remove_confirmed_transactions([tx['txid'] for tx in valid_txs])
    print(f"[MINER] Bloco {new_block['index']} minerado com {len(valid_txs)} transações.")
    return new_block

class Blockchain:
    def __init__(self):
        self.chain = []
        self.fusohorario = ZoneInfo("America/Sao_Paulo")
        self.node_manager = NodeManager()
        self.utxo_set = UTXOSet()
        self.consensus = ProofOfEnergy(self)
        self.load_chain()
        self._rebuild_utxos()

    def load_chain(self):
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        os.makedirs(data_dir, exist_ok=True)
        self.blockchain_file = os.path.join(data_dir, 'blockchain.json')
        try:
            with open(self.blockchain_file, 'r') as f:
                self.chain = json.load(f)
        except FileNotFoundError:
            self.create_genesis_block()

    def create_genesis_block(self):
        # Chave pública fixa que você já possui (não comprimida)
        public_key_full  = "04" + "8f231d59aa2419510f26929b9668d2093d4ceacfe0559a0ab2c654b2faab27a8ee767bb4efec715b6706b9f1750258f92357664d3eb6b6b30d7d6f57d106d555"
        # Comprime a chave pública para guardar na saída
        public_key_compressed = compress_pubkey(public_key_full)
        # Endereço fixo que você já possui
        address = "1ef0d9d207f83073454e6ac197b331cf626c0973"

        genesis_tx = {
            'txid': 'genesis-tx-1',
            'inputs': [],
            'outputs': [
                {
                    'address': address,
                    'amount': 1000.0,
                    'public_key': public_key_compressed
                }
            ],
            'type': 'genesis',
            'date': self.current_time(),
            'status': 'confirmed'
        }

        genesis = {
            'index': 0,
            'timestamp': self.current_time(),
            'consolidated_energy': 0,
            'transactions': [genesis_tx],
            'previous_hash': '0'*64,
            'node_count': 0
        }
        genesis['hash'] = self.calculate_hash(genesis)
        self.chain.append(genesis)
        self.save_chain()

    def _rebuild_utxos(self):
        self.utxo_set.utxos = {}  # limpa
        for block in self.chain:
            for tx in block.get('transactions', []):
                # Remove UTXOs gastos
                for inp in tx.get('inputs', []):
                    self.utxo_set.spend_utxo(inp['txid'], inp['index'])
                # Adiciona novos UTXOs dos outputs
                for idx, out in enumerate(tx.get('outputs', [])):
                    public_key = out.get('public_key', '') or out.get('locking_script', '')
                    self.utxo_set.add_utxo(out['address'], tx['txid'], idx, out['amount'], public_key)
        self.utxo_set.save_utxos()

    def add_block(self):
        daily_data = self.node_manager.aggregate_daily_data()
        if not self.consensus.validate_node(
            node_id="daily_aggregate",
            reported_energy=daily_data['total_energy']
        ):
            raise Exception("Consenso de energia falhou")

        last_block = self.chain[-1]
        new_block = {
            'index': len(self.chain),
            'timestamp': self.current_time(),
            'consolidated_energy': daily_data['total_energy'],
            'transactions': [],
            'node_count': daily_data['valid_nodes'],
            'previous_hash': last_block['hash']
        }

        # Garante que todas as chaves públicas das outputs estejam comprimidas
        for tx in daily_data.get('transactions', []):
            for out in tx.get('outputs', []):
                pubkey = out.get('public_key', '')
                if pubkey:
                    out['public_key'] = compress_pubkey(pubkey)

        new_block['transactions'] = daily_data.get('transactions', [])
        new_block['hash'] = self.calculate_hash(new_block)
        reward = self.consensus.mint_tokens(daily_data['total_energy'])
        new_block['reward'] = reward

        for tx in new_block['transactions']:
            for inp in tx.get('inputs', []):
                self.utxo_set.spend_utxo(inp['txid'], inp['index'])
            for idx, out in enumerate(tx.get('outputs', [])):
                public_key = out.get('public_key', '')  # já comprimida aqui
                self.utxo_set.add_utxo(out['address'], tx['txid'], idx, out['amount'], public_key)
        self.utxo_set.save_utxos()

        self.chain.append(new_block)
        self.save_chain()
        return new_block

    def calculate_hash(self, block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def save_chain(self):
        # Garante que o caminho do arquivo está definido
        if not hasattr(self, 'blockchain_file'):
            self.blockchain_file = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..', 'data', 'blockchain.json')
            )
        with open(self.blockchain_file, 'w') as f:
            json.dump(self.chain, f, indent=2)

    def current_time(self):
        return datetime.now(self.fusohorario).isoformat()


# blockchain/core.py

def get_chain():
    if _blockchain is None:
        init_blockchain()
    return _blockchain.chain
