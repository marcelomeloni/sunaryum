import random
import json
import time
from machine import Pin, ADC  # Hardware real

class EnergyMonitor:
    def __init__(self, node_id):
        self.node_id = node_id
        self.voltage_pin = ADC(Pin(32))
        self.current_pin = ADC(Pin(33))
        
    def read_sensors(self):
        return {
            'volts': self.voltage_pin.read() * (3.3 / 4095),
            'amps': self.current_pin.read() * (3.3 / 4095),
            'timestamp': time.time()
        }

    def save_hourly_data(self):
        reading = self.read_sensors()
        energy_j = reading['volts'] * reading['amps'] * 3600
        
        with open('/data/horarios.json', 'a') as f:
            json.dump({
                'node_id': self.node_id,
                'energy': energy_j,
                'timestamp': reading['timestamp']
            }, f)
            f.write('\n')

    def main_loop(self):
        while True:
            self.save_hourly_data()
            time.sleep(3600)  # Espera 1 hora

# Uso no Arduino
monitor = EnergyMonitor("NODE-001")
monitor.main_loop()