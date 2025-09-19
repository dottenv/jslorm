import os

class DatabaseConfig:
    def __init__(self):
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/app')
        self.DATABASE_BACKUP_DIR = os.getenv('DATABASE_BACKUP_DIR', 'backups')
        self.DATABASE_AUTO_BACKUP = os.getenv('DATABASE_AUTO_BACKUP', 'true').lower() == 'true'
        self.DATABASE_BACKUP_INTERVAL = int(os.getenv('DATABASE_BACKUP_INTERVAL', '3600'))
        
    def get_db_path(self) -> str:
        db_dir = os.path.dirname(self.DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        return self.DATABASE_PATH
    
    def get_backup_dir(self) -> str:
        if not os.path.exists(self.DATABASE_BACKUP_DIR):
            os.makedirs(self.DATABASE_BACKUP_DIR, exist_ok=True)
        return self.DATABASE_BACKUP_DIR