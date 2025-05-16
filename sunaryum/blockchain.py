import hashlib
import json
from datetime import datetime

class Blockchain:
    def __init__(self):
        # Inicia a cadeia de blocos e cria o bloco gênesis
        self.chain = []
        self.create_genesis()

    def calculateHash(self, block):
        
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def block(self, index, total_energy, tx, previous_hash):
        
        blk = {
            'index': index,
            'timestamp': datetime.utcnow().isoformat(),
            'energy_generated': total_energy,
            'transactions': tx,
            'previous_hash': previous_hash
        }
        blk['hash'] = self.calculateHash(blk)
        return blk

    def create_genesis(self):
        
        kwedo = "dsdsdsd"  # substituir pela wallet futuramente
        index = 1
        total_energy = 0
        tx = {
            'amount': 1000,
            'from': 'system',
            'to': kwedo
        }
        previous_hash = '0' * 64  # hash fictício do bloco gênesis
        genesis = self.block(index, total_energy, [tx], previous_hash)
        self.chain.append(genesis)
        return genesis

    def total_energy(self):
        """
        Placeholder para lógica de cálculo de energia gerada em um bloco.
        """
        return 0

    def tx(self):
        
        return []

    def previous_hash(self):
        
        return self.chain[-1]['hash'] if self.chain else '0' * 64

    def create_Block(self):
        
        # Validação de integridade
        if self.chain and self.previous_hash() != self.chain[-1]['hash']:
            raise ValueError("previous_hash não confere com o último bloco da cadeia")

        index = len(self.chain) + 1
        energy = self.total_energy()
        transactions = self.tx()
        prev_hash = self.previous_hash()

        new_blk = self.block(index, energy, transactions, prev_hash)
        self.chain.append(new_blk)
        return new_blk


# Exemplo de uso:
if __name__ == "__main__":
    bc = Blockchain()
    print("Gênesis:", bc.chain[0])
    blk2 = bc.create_Block()
    print("Bloco 2:", blk2)
