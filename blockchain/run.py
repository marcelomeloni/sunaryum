# run.py

# run.py

import sys
import os

# Adiciona a raiz do projeto ao sys.path antes de qualquer import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from transactions.mempool import Mempool
from blockchain.core import Blockchain
from transactions.utxo import is_valid_transaction
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

    # Prepara dados do dia com as transações válidas
    daily_data = blockchain.node_manager.aggregate_daily_data()
    daily_data['transactions'] = valid_txs

    # Força o node_manager a retornar esse daily_data
    blockchain.node_manager.aggregate_daily_data = lambda: daily_data

    # Adiciona bloco
    new_block = blockchain.add_block()

    # Remove as transações mineradas da mempool
    mempool.remove_confirmed_transactions([tx['txid'] for tx in valid_txs])

    print(f"[MINER] Bloco {new_block['index']} minerado com {len(valid_txs)} transações.")
    return new_block

if __name__ == "__main__":
    print("[RUN] Inicializando blockchain e mempool...")
    blockchain = Blockchain()
    mempool = Mempool(blockchain.utxo_set)

    print("[RUN] Iniciando mineração única...")
    new_block = mine_mempool_transactions(blockchain, mempool)

    if new_block:
        print(f"[RUN] Bloco minerado com sucesso! Hash: {new_block['hash']}")
    else:
        print("[RUN] Nenhum bloco foi minerado.")
