import json
from datetime import datetime
from zoneinfo import ZoneInfo
from .utxo import is_valid_transaction, UTXOSet

class Mempool:
    def __init__(self, utxo_set: UTXOSet, path='server/transactions/mempool.json'):
        self.transactions = []
        self.fusohorario = ZoneInfo("America/Sao_Paulo")
        self.path = path
        self.utxo_set = utxo_set
        self.load_mempool()

    def add_transaction(self, tx):
        if not is_valid_transaction(tx, self.utxo_set):
            raise Exception("Transação inválida: fundos insuficientes ou inputs não encontrados")

        for inp in tx.get('inputs', []):
            self.utxo_set.spend_utxo(inp['address'], inp['txid'])
        self.utxo_set.save_utxos()

        tx['timestamp'] = datetime.now(self.fusohorario).isoformat()
        self.transactions.append(tx)
        self.save_mempool()

    def clear_mempool(self):
        self.transactions = []
        self.save_mempool()

    def load_mempool(self):
        try:
            with open(self.path, 'r') as f:
                self.transactions = json.load(f)
        except FileNotFoundError:
            self.transactions = []

    def save_mempool(self):
        with open(self.path, 'w') as f:
            json.dump(self.transactions, f, indent=2)
