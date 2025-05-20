from flask import Blueprint, request, jsonify
import os
import json
import time

node_bp = Blueprint('node', __name__)

# Garante que a pasta para blocos exista
BLOCK_FOLDER = 'blocos_recebidos'
os.makedirs(BLOCK_FOLDER, exist_ok=True)

@node_bp.route('/upload_block', methods=['POST'])
def upload_block():
    try:
        block = request.get_json()
        if not block:
            return jsonify({'error': 'Empty request'}), 400

        # Validação básica
        required_fields = ['node_id', 'readings']
        if not all(field in block for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        if not isinstance(block['readings'], list) or len(block['readings']) == 0:
            return jsonify({'error': 'Invalid readings data'}), 400

        # Garante que a pasta existe
        os.makedirs(BLOCK_FOLDER, exist_ok=True)

        # Nome do arquivo com timestamp e node_id
        filename = f"{BLOCK_FOLDER}/{block['node_id']}_{int(time.time())}.json"
        
        with open(filename, 'w') as f:
            json.dump(block, f, indent=2)

        print(f"[UPLOAD] Block saved: {filename}")
        return jsonify({
            'message': 'Block received',
            'saved_as': filename,
            'readings_count': len(block['readings'])
        }), 200

    except Exception as e:
        print(f"[ERROR] Failed to process block: {e}")
        return jsonify({'error': 'Internal server error'}), 500