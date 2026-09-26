import os
from dataclasses import dataclass


@dataclass
class ConfigBot:
    TOKEN: str = os.getenv('BOT_TOKEN', '')
    

