from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

class TransactionManager:
    def __init__(self, db_driver):
        self.db_driver = db_driver
        self.transaction_lock = asyncio.Lock()
        self.rollback_data = None

    async def __aenter__(self):
        await self.transaction_lock.acquire()
        # Сохраняем состояние для отката
        self.rollback_data = await self.db_driver._load_data()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                # Откатываем изменения при ошибке
                await self.db_driver._save_data(self.rollback_data)
        finally:
            self.transaction_lock.release()

class EncryptionManager:
    @staticmethod
    def encrypt_field(value: str, key: str = "default") -> str:
        # Простое шифрование для демонстрации
        import base64
        encoded = base64.b64encode(f"{key}:{value}".encode()).decode()
        return f"ENC:{encoded}"

    @staticmethod
    def decrypt_field(encrypted_value: str, key: str = "default") -> str:
        if not encrypted_value.startswith("ENC:"):
            return encrypted_value
        
        import base64
        try:
            decoded = base64.b64decode(encrypted_value[4:]).decode()
            stored_key, value = decoded.split(":", 1)
            if stored_key == key:
                return value
        except:
            pass
        return encrypted_value