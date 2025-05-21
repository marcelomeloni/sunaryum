class ProofOfEnergy:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.energy_tolerance = 0.05  # 5% de tolerância

    def validate_node(self, node_id, reported_energy):
        return True

    def mint_tokens(self, validated_energy):
        """Calcula tokens baseado na energia validada (Wh para BTLF)"""
        
        return validated_energy / 20000
