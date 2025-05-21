from flask import Blueprint, jsonify, request
from blockchain.wallet import Wallet
from blockchain.core import init_blockchain
from mnemonic import Mnemonic
from ecdsa import SigningKey, SECP256k1


def wallet_bp(utxo_set, mempool):
    bp = Blueprint('wallet', __name__)
    
    @bp.route('/import', methods=['POST'])
    def import_wallet():
        data = request.get_json()
        mnemonic = data.get('mnemonic')
        if not mnemonic:
            return jsonify({'error': 'Mnemonic required'}), 400

        mnemo = Mnemonic('english')
        if not mnemo.check(mnemonic):
            return jsonify({'error': 'Invalid mnemonic'}), 400

        try:
            seed = mnemo.to_seed(mnemonic, passphrase="")
            priv_key_bytes = seed[:32]
            priv = SigningKey.from_string(priv_key_bytes, curve=SECP256k1)
            pub = priv.get_verifying_key()
            address = Wallet.generate_address(pub)

            return jsonify({
                'mnemonic': mnemonic,
                'address': address,
                'public_key': pub.to_string().hex(),
                'private_key': priv.to_string().hex()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/new', methods=['GET'])
    def new_wallet():
        w = Wallet.create()
        return jsonify({
            'mnemonic': w.mnemonic,
            'address': w.address,
            'public_key': w.public_key.to_string().hex(),
            'private_key': w.private_key.to_string().hex()
        })

    @bp.route('/balance/<address>', methods=['GET'])
    def get_balance(address):
        try:
            confirmed_balance = utxo_set.get_balance(address) or 0
            confirmed_utxos = [u.to_dict() for u in utxo_set.find_utxos(address) or []]

            pending_received = 0
            pending_sent = 0

            # calcula pendentes via UTXO
            for tx in mempool.get_all_transactions():
                # recebimentos pendentes (outputs para este address que não são change):
                for out in tx.get('outputs', []):
                    if out.get('address') == address and tx.get('recipient') == address:
                        pending_received += tx.get('amount', 0)
                # envios pendentes => se este address é o sender
              if tx.get('sender') == address:
                    pending_sent += tx.get('amount', 0)

            total = confirmed_balance + pending_received - pending_sent
            return jsonify({
                'address': address,
                'confirmed_balance': confirmed_balance,
                'pending_received': pending_received,
                'pending_sent': pending_sent,
                'total_balance': total,
                'utxos': confirmed_utxos,
                'pending_count': len([
                    tx for tx in mempool.get_all_transactions()
                    if tx.get('sender') == address or tx.get('recipient') == address
                ])
            })
        except Exception as e:
            print(f"[ERROR] Erro no balance: {str(e)}")
            return jsonify({'error': 'Internal error', 'details': str(e)}), 500

    @bp.route('/transactions/<address>', methods=['GET'])
    def wallet_transactions(address):
        blockchain = init_blockchain()
        history = []

        # --- Transações Confirmadas ---
        for block in blockchain.chain:
            ts = block.get('timestamp')
            for tx in block.get('transactions', []):
                sender = tx.get('sender')
                sent = 0
                received = 0

                if sender == address:
                    # Valor ENVIADO: soma dos outputs que não são para o próprio address
                    sent = sum(
                        out.get('amount', 0) for out in tx.get('outputs', [])
                        if out.get('address') != address
                    )
                else:
                    # Valor RECEBIDO: soma dos outputs para o address
                    received = sum(
                        out.get('amount', 0) for out in tx.get('outputs', [])
                        if out.get('address') == address
                    )

                if sent > 0:
                    history.append({'txid': tx['txid'], 'type': 'sent (confirmed)', 'amount': sent, 'date': ts})
                if received > 0:
                    history.append({'txid': tx['txid'], 'type': 'received (confirmed)', 'amount': received, 'date': ts})

        # --- Transações Pendentes ---
        for tx in mempool.get_all_transactions():
            txid = tx.get('txid')
            ts = tx.get('timestamp') or tx.get('date')
            sender = tx.get('sender')
            sent_pending = 0
            received_pending = 0

            if sender == address:
                # Valor ENVIADO pendente: outputs para outros endereços
                sent_pending = sum(
                    out.get('amount', 0) for out in tx.get('outputs', [])
                    if out.get('address') != address
                )
            else:
                # Valor RECEBIDO pendente: outputs para o address
                received_pending = sum(
                    out.get('amount', 0) for out in tx.get('outputs', [])
                    if out.get('address') == address
                )

            if sent_pending > 0:
                history.append({'txid': txid, 'type': 'sent (pending)', 'amount': sent_pending, 'date': ts})
            if received_pending > 0:
                history.append({'txid': txid, 'type': 'received (pending)', 'amount': received_pending, 'date': ts})

        # Ordenar por data
        history.sort(key=lambda x: x['date'], reverse=True)
        return jsonify({'transactions': history})

    return bp 
