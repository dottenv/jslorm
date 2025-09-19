#!/usr/bin/env python3
import asyncio
import sys
import os
import argparse
from .config import DatabaseConfig
from .driver import DatabaseDriver
from .migrations import MigrationEngine, ModelRegistry

class CLI:
    def __init__(self):
        self.config = DatabaseConfig()
        self.db = DatabaseDriver(self.config.get_db_path())
        self.migration_engine = MigrationEngine(self.db)

    async def init_db(self):
        """Инициализация БД и поиск моделей"""
        print("🔍 Discovering models...")
        ModelRegistry.discover_models()
        
        models = ModelRegistry.get_models()
        if not models:
            print("⚠️  No models found. Make sure your models inherit from BaseModel.")
            return
        
        print(f"📊 Found {len(models)} models")
        await self.migration_engine.init_migration_table()
        print("✅ Database initialized")

    async def db_upgrade(self):
        """Применение миграций"""
        print("🔍 Discovering models...")
        ModelRegistry.discover_models()
        
        print("🔄 Applying migrations...")
        await self.migration_engine.upgrade()

    async def db_status(self):
        """Статус миграций"""
        print("🔍 Discovering models...")
        ModelRegistry.discover_models()
        
        await self.migration_engine.show_status()

    async def backup(self, path: str = None):
        if path is None:
            backup_dir = self.config.get_backup_dir()
            path = os.path.join(backup_dir, f"backup_{int(__import__('time').time())}.json")
        await self.db.backup(path)
        print(f"✅ Backup created: {path}")

    async def restore(self, backup_path: str):
        if not os.path.exists(backup_path):
            print(f"❌ Backup file not found: {backup_path}")
            return
        await self.db.restore(backup_path)
        print("✅ Database restored")

    async def stats(self):
        stats = await self.db.get_stats()
        print("\n📊 Database Statistics:")
        print("-" * 30)
        for table_name, table_stats in stats["tables"].items():
            print(f"{table_name}: {table_stats['record_count']} records")
        print("-" * 30)

def main():
    parser = argparse.ArgumentParser(description='JSLORM CLI - Flask-SQLAlchemy style')
    parser.add_argument('command', choices=[
        'init', 'db-upgrade', 'db-status', 'backup', 'restore', 'stats'
    ])
    parser.add_argument('--path', help='Path for backup/restore')
    
    args = parser.parse_args()
    cli = CLI()
    
    try:
        if args.command == 'init':
            asyncio.run(cli.init_db())
        elif args.command == 'db-upgrade':
            asyncio.run(cli.db_upgrade())
        elif args.command == 'db-status':
            asyncio.run(cli.db_status())
        elif args.command == 'backup':
            asyncio.run(cli.backup(args.path))
        elif args.command == 'restore':
            if not args.path:
                print("❌ --path required for restore")
                sys.exit(1)
            asyncio.run(cli.restore(args.path))
        elif args.command == 'stats':
            asyncio.run(cli.stats())
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()