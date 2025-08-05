# utils.py
import random

class DataGenerator:
    """Generate a rows×cols matrix of random ints."""
    @staticmethod
    def generate(rows, cols):
        return [
            [random.randint(1, 100) for _ in range(cols)]
            for _ in range(rows)
        ]
