# blockchain/core.py
import hashlib
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from nodes.node_manager import NodeManager
from transactions.utxo import UTXOSet
from blockchain.consensus import ProofOfEnergy

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
        os.makedirs('data', exist_ok=True)
        try:
            with open('data/blockchain.json', 'r') as f:
                self.chain = json.load(f)
        except FileNotFoundError:
            self.create_genesis_block()

    def create_genesis_block(self):
        genesis = {
            'index': 0,
            'timestamp': self.current_time(),
            'consolidated_energy': 0,
            'transactions': [],
            'previous_hash': '0'*64,
            'node_count': 0
        }
        genesis['hash'] = self.calculate_hash(genesis)
        self.chain.append(genesis)
        self.save_chain()

    def _rebuild_utxos(self):
        self.utxo_set.utxos = {}
        for block in self.chain:
            for tx in block.get('transactions', []):
                for inp in tx.get('inputs', []):
                    self.utxo_set.spend_utxo(inp['address'], inp['txid'])
                for out in tx.get('outputs', []):
                    self.utxo_set.add_utxo(out['address'], tx['txid'], out['amount'])
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
            'transactions': daily_data['transactions'],
            'node_count': daily_data['valid_nodes'],
            'previous_hash': last_block['hash']
        }
        new_block['hash'] = self.calculate_hash(new_block)
        reward = self.consensus.mint_tokens(daily_data['total_energy'])
        new_block['reward'] = reward

        for tx in daily_data.get('transactions', []):
            for inp in tx.get('inputs', []):
                self.utxo_set.spend_utxo(inp['address'], inp['txid'])
            for out in tx.get('outputs', []):
                self.utxo_set.add_utxo(out['address'], tx['txid'], out['amount'])
        self.utxo_set.save_utxos()

        self.chain.append(new_block)
        self.save_chain()
        return new_block

    def calculate_hash(self, block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def save_chain(self):
        with open('data/blockchain.json', 'w') as f:
            json.dump(self.chain, f, indent=2)

    def current_time(self):
        return datetime.now(self.fusohorario).isoformat()