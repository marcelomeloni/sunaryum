# arduino/nodes/node_manager.py

import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests

class NodeManager:
    def __init__(self):
        self.fusohorario = ZoneInfo("America/Sao_Paulo")
        self.nodes = {}
        self.load_nodes()

    def load_nodes(self):
        if os.path.exists('nodes.json'):
            with open('nodes.json', 'r') as f:
                self.nodes = json.load(f)

    def save_nodes(self):
        with open('nodes.json', 'w') as f:
            json.dump(self.nodes, f, indent=2)

    def register_node(self, node_id, wallet_address):
        self.nodes[node_id] = {
            'wallet': wallet_address,
            'last_validation': None,
            'energy_history': []
        }
        self.save_nodes()

    def load_energy_data_from_nodes(self):
        # Aqui você pode implementar a leitura dos arquivos horarios.json dos nodes, 
        # ou coletar via API/endpoint os dados horários e armazenar em self.nodes[node_id]['energy_history']

        for node_id in self.nodes.keys():
            path = f'/data/{node_id}_horarios.json'  # Exemplo de arquivo com dados do node
            if os.path.exists(path):
                with open(path, 'r') as f:
                    self.nodes[node_id]['energy_history'] = [json.loads(line) for line in f]

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
        print(f"[NodeManager] Validando nodo {node_id}: energia reportada = {reported_energy} (sempre válido)")
        return True

    def send_daily_report(self, server_url):
        daily_data = self.aggregate_daily_data()
        payload = {
            'date': datetime.now(self.fusohorario).strftime('%Y-%m-%d'),
            'total_energy': daily_data['total_energy'],
            'valid_nodes': daily_data['valid_nodes'],
            'transactions': daily_data['transactions']
        }
        try:
            response = requests.post(server_url, json=payload)
            if response.status_code == 200:
                print("[NodeManager] Relatório diário enviado com sucesso.")
            else:
                print(f"[NodeManager] Falha ao enviar relatório: {response.status_code}")
        except Exception as e:
            print(f"[NodeManager] Erro ao enviar relatório diário: {e}")

if __name__ == "__main__":
    nm = NodeManager()
    nm.load_nodes()
    nm.load_energy_data_from_nodes()
    nm.send_daily_report("http://localhost:5000/node/daily_report")
