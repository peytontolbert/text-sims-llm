
# File: needs_system.py
from typing import List, Dict

class Needs:
    def __init__(self):
        self.values = {
            'energy': 100,
            'hunger': 100,
            'hygiene': 100,
            'fun': 100,
            'bladder': 100,
            'social': 100
        }
        self.decay_rates = {
            'energy': 0.5,
            'hunger': 0.3,
            'hygiene': 0.2,
            'fun': 0.4,
            'bladder': 0.6,
            'social': 0.2
        }
        self.thresholds = {
            'critical': 20,
            'warning': 40,
            'comfortable': 70
        }

    def update(self, delta_time: float):
        for need, value in self.values.items():
            decay = self.decay_rates[need] * delta_time
            self.values[need] = max(0, min(100, value - decay))

    def modify(self, need: str, amount: float):
        if need in self.values:
            self.values[need] = max(0, min(100, self.values[need] + amount))

    def get_urgent_needs(self, threshold: float = 30.0) -> List[str]:
        return [need for need, value in self.values.items() if value < threshold]

    def get_need_status(self) -> Dict[str, str]:
        status = {}
        for need, value in self.values.items():
            if value < self.thresholds['critical']:
                status[need] = 'critical'
            elif value < self.thresholds['warning']:
                status[need] = 'warning'
            elif value < self.thresholds['comfortable']:
                status[need] = 'moderate'
            else:
                status[need] = 'good'
        return status
