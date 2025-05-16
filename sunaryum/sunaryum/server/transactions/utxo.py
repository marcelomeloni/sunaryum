import json
import os
class UTXOSet:
    def __init__(self):
        self.utxos = {}
        self.path = "data/utxos.json"  # Caminho corrigido
        self.load_utxos()

    def add_utxo(self, address, txid, amount):
        if address not in self.utxos:
            self.utxos[address] = []
        self.utxos[address].append({"txid": txid, "amount": amount})

    def spend_utxo(self, address, txid):
        if address in self.utxos:
            self.utxos[address] = [u for u in self.utxos[address] if u["txid"] != txid]

    def get_balance(self, address):
        return sum(u["amount"] for u in self.utxos.get(address, []))

    def load_utxos(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "r") as f:
                self.utxos = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.utxos = {}

    def save_utxos(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)  # Cria diretório
        with open(self.path, "w") as f:
            json.dump(self.utxos, f, indent=2)


def is_valid_transaction(tx, utxo_set: UTXOSet):
    # soma valores dos inputs
    total_input = 0
    for inp in tx.get("inputs", []):
        utxos = utxo_set.utxos.get(inp["address"], [])
        match = next((u for u in utxos if u["txid"] == inp["txid"]), None)
        if not match:
            return False
        total_input += match["amount"]

    # soma valores das outputs
    total_output = sum(out.get("amount", 0) for out in tx.get("outputs", []))

    return total_input >= total_output
