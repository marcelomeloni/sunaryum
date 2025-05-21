from flask import Flask, Response
from argparse import ArgumentParser
from flask_cors import CORS
from blockchain.wallet_api import wallet_bp
from blockchain.tx_api import tx_bp
from blockchain.chain_api import chain_bp
from transactions.utxo import UTXOSet
from transactions.mempool import Mempool
from blockchain.core import init_blockchain  
from routes.node_routes import node_bp  # seu blueprint para node

def create_app():
    app = Flask(__name__)

    # Habilitar CORS nas rotas
    CORS(app, resources={ 
        r"/wallet/*": {"origins": "*"},
        r"/transaction/*": {"origins": "*"},
        r"/chain/*": {"origins": "*"},
        r"/node/*": {"origins": "*"}  # CORS para node também
    })

    @app.after_request
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        if request.method == 'OPTIONS':
            # Adiciona cabeçalhos CORS para as requisições OPTIONS
            response = Response()
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
            return response
        return response

    # ✅ Inicializa a blockchain e carrega o singleton
    blockchain = init_blockchain()

    utxo_set = UTXOSet()
    mempool = Mempool(utxo_set)
    utxo_set.load_utxos()

    app.register_blueprint(wallet_bp(utxo_set, mempool), url_prefix='/wallet')
    app.register_blueprint(tx_bp(utxo_set, mempool, blockchain), url_prefix='/transaction')
    app.register_blueprint(chain_bp(), url_prefix='/chain')
    app.register_blueprint(node_bp, url_prefix='/node')

    return app

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()

    app = create_app()
    app.run(host='0.0.0.0', port=args.port, debug=True)
