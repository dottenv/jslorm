# Changelog

All notable changes to JSLORM will be documented in this file.

## [1.0.0] - 2024-01-XX

### Added
- 🚀 Advanced JSON-based ORM with async support
- 🔍 Query Builder with operators (gt, lt, like, in, etc.)
- ⚡ Automatic indexing and query caching
- 🔗 Foreign keys and relationships support
- 📊 Aggregation functions (count, sum, avg, min, max)
- 🛡️ Schema validation and unique constraints
- 📈 Performance monitoring and metrics
- 🔧 CLI commands for migrations (Flask-SQLAlchemy style)
- 🗂️ Automatic model discovery from multiple files
- 💾 Backup/restore functionality
- 🔄 Middleware support for logging and custom logic
- 📦 Data compression for production use
- 🏥 Health checks for monitoring
- 🎯 Pagination support for large datasets

### Features
- **Models**: Pydantic-based models with auto-registration
- **Migrations**: Automatic model discovery and migration system
- **CLI**: `jslorm init`, `jslorm db-upgrade`, `jslorm db-status`
- **Performance**: Caching, indexing, compression
- **Monitoring**: Metrics, logging, health checks
- **Production Ready**: No external dependencies, async/await

### CLI Commands
```bash
jslorm init         # Initialize database
jslorm db-upgrade   # Apply migrations
jslorm db-status    # Show migration status
jslorm backup       # Create backup
jslorm restore      # Restore from backup
jslorm stats        # Show database statistics
```

### Example Usage
```python
from jslorm import Database, BaseModel, BaseRepository, foreign_key

class User(BaseModel):
    name: str
    email: str
    __table_name__ = "users"
    __indexes__ = ["email"]

db = Database("myapp")
await db.init_db()  # Auto-discovers models
```