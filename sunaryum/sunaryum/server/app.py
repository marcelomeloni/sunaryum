# app.py (Backend Flask)
import sys
import os
from flask import Flask, jsonify, request, render_template
from blockchain.core import Blockchain
from nodes.node_manager import NodeManager
from transactions.mempool import Mempool
from blockchain.wallet import Wallet
from transactions.utxo import UTXOSet, is_valid_transaction
from mnemonic import Mnemonic
from hashlib import sha256
import json
import threading
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
app = Flask(__name__, static_folder='static', template_folder='templates')

# Inicialização dos componentes
blockchain = Blockchain()
utxos = UTXOSet()
mempool = Mempool(utxos)
node_manager = NodeManager()

class Miner:
    def __init__(self, blockchain, mempool, utxos):
        self.blockchain = blockchain
        self.mempool = mempool
        self.utxos = utxos
        self.mining = False

    def start_mining(self):
        self.mining = True
        while self.mining:
            if len(mempool.transactions) > 0:
                new_block = self.blockchain.mine_block(self.mempool.transactions)
                if new_block:
                    self.utxos.process_block(new_block)
                    self.mempool.clear()
            time.sleep(10)

miner = Miner(blockchain, mempool, utxos)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/wallet/new', methods=['GET'])
def new_wallet():
    mnemo = Mnemonic("english")
    seed = mnemo.generate(strength=128)
    privkey = sha256(seed.encode()).hexdigest()
    pubkey = sha256(privkey.encode()).hexdigest()
    address = sha256(pubkey.encode()).hexdigest()[:40]
    
    return jsonify({
        'seed': seed,
        'address': address,
        'private_key': privkey
    })

@app.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    return jsonify({
        'address': address,
        'balance': utxos.get_balance(address),
        'confirmed': True
    })

@app.route('/transaction', methods=['POST'])
def create_transaction():
    data = request.json
    try:
        tx = {
            'txid': sha256(json.dumps(data).encode()).hexdigest(),
            'inputs': data['inputs'],
            'outputs': data['outputs']
        }
        
        if is_valid_transaction(tx, utxos):
            mempool.add_transaction(tx)
            return jsonify({'status': 'success', 'txid': tx['txid']})
        return jsonify({'status': 'error', 'message': 'Invalid transaction'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/mempool', methods=['GET'])
def get_mempool():
    return jsonify(mempool.transactions)

@app.route('/mine', methods=['POST'])
def start_mining():
    if not miner.mining:
        threading.Thread(target=miner.start_mining).start()
        return jsonify({'status': 'mining started'})
    return jsonify({'status': 'already mining'})

@app.route('/blocks', methods=['GET'])
def get_blocks():
    return jsonify(blockchain.chain)

if __name__ == '__main__':
    # UTXO inicial
    genesis_address = sha256(sha256(b"genesis").hexdigest().encode()).hexdigest()[:40]
    utxos.add_utxo(genesis_address, sha256(b"genesis").hexdigest(), 1000000)
    
    app.run(port=5000, debug=True)