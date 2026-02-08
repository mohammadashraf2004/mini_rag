import os
from helpers.config import get_settings,Settings
import random
import string

class BaseController:
    
    def __init__(self):

        self.settings = get_settings()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.file_dir = os.path.join(self.base_dir, "assets/files")

    def generate_random_string(self, length: int = 8):
        letters = string.ascii_letters + string.digits
        return ''.join(random.choice(letters) for _ in range(length))