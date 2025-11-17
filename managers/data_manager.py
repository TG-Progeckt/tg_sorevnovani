import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def _get_file_path(self, filename: str) -> str:
        return os.path.join(self.data_dir, f"{filename}.json")

    def load_data(self, filename: str) -> Dict[str, Any]:
        """Загрузка данных из JSON файла"""
        filepath = self._get_file_path(filename)
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Ошибка загрузки {filename}: {e}")
            return {}

    def save_data(self, data: Dict[str, Any], filename: str) -> bool:
        """Сохранение данных в JSON файл"""
        filepath = self._get_file_path(filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения {filename}: {e}")
            return False

    def load_promo_codes(self, promocodes_file: str) -> Dict[str, bool]:
        """Загрузка промокодов из TXT файла"""
        try:
            if not os.path.exists(promocodes_file):
                with open(promocodes_file, 'w', encoding='utf-8') as f:
                    for i in range(1, 51):
                        f.write(f"TG2024{i:03d}\n")

            used_codes = self.load_data('used_promo_codes')

            with open(promocodes_file, 'r', encoding='utf-8') as f:
                codes = {}
                for line in f:
                    code = line.strip().split(' # ')[0]
                    if code:
                        codes[code] = code in used_codes
                return codes
        except Exception as e:
            logger.error(f"Ошибка загрузки промокодов: {e}")
            return {}