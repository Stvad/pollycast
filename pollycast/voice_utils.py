import os
import random


def random_voice_id():
    return random.choice(os.environ['Voices'].split(","))
