# nodes/node_manager.py
import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

class NodeManager:
    def __init__(self):
        self.fusohorario = ZoneInfo("America/Sao_Paulo")
        self.nodes = {}
        self.load_nodes()

    def load_nodes(self):
        if os.path.exists('nodes.json'):
            with open('nodes.json', 'r') as f:
                self.nodes = json.load(f)

    def register_node(self, node_id, wallet_address):
        self.nodes[node_id] = {
            'wallet': wallet_address,
            'last_validation': None,
            'energy_history': []
        }
        self.save_nodes()

    def save_nodes(self):
        with open('nodes.json', 'w') as f:
            json.dump(self.nodes, f, indent=2)

    def aggregate_daily_data(self):
        daily_data = {
            'total_energy': 0,
            'valid_nodes': 0,
            'transactions': []
        }
        
        cutoff_time = datetime.now(self.fusohorario) - timedelta(days=1)
        
        for node_id, data in self.nodes.items():
            node_energy = sum(
                entry['energy'] for entry in data['energy_history']
                if datetime.fromisoformat(entry['timestamp']) >= cutoff_time
            )
            
            if self.validate_node_energy(node_id, node_energy):
                daily_data['total_energy'] += node_energy
                daily_data['valid_nodes'] += 1
                self.nodes[node_id]['energy_history'] = []

        return daily_data

    def validate_node_energy(self, node_id, reported_energy):
        """
        Validação de energia fictícia: sempre retorna True enquanto não houver hardware.
        """
        # Placeholder: aceita qualquer valor de energia
        print(f"[NodeManager] Validando nodo {node_id}: energia reportada = {reported_energy} (sempre válido)")
        return True
