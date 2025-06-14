import os
import random
from pathlib import Path
from dotenv import load_dotenv

class GoogleKey:
    def __init__(self, pattern: str="GOOGLE_API_KEY", num_keys: int = 1):
        env_path = Path(__file__).resolve().parents[1] / ".env"
        if not load_dotenv(dotenv_path=env_path):
            raise FileNotFoundError(f"Không tìm thấy .env tại {env_path}")

        self.list = []
        for i in range(num_keys):
            key_name = f"{pattern}_{i}"
            val = os.getenv(key_name)
            if val:
                self.list.append(val)
        if not self.list:
            raise RuntimeError("Chưa có API key nào được load — kiểm tra tên biến và .env")

    def get_key(self):
        return random.choice(self.list)
