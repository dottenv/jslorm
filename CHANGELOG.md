# Changelog

All notable changes to JSLORM will be documented in this file.

## [1.1.0] - 2024-01-XX

### Fixed
- 🐛 **CRITICAL**: Fixed DatabaseDriver.select() to support query_builder parameter
- 🐛 **CRITICAL**: Removed broken @timed_operation and @cached decorators
- 🐛 **CRITICAL**: Fixed BaseRepository to use correct DatabaseDriver API
- ✅ Fixed query operators (age__gte=18, name__like="John") in BaseRepository.find()
- 🔄 Fixed QueryBuilder.apply_filters() integration
- 🔍 Improved model discovery in migrations

### Changed
- 📝 Synchronized BaseRepository with DatabaseDriver API
- ⚡ QueryBuilder now properly integrated with select() method
- 🔧 Simplified decorator system (removed problematic decorators)

## [1.0.2] - 2024-01-XX

### Fixed
- 🐛 Fixed Pydantic v2 compatibility (`model_fields` instead of `__fields__`)
- ✅ Fixed schema generation for newer Pydantic versions

## [1.0.1] - 2024-01-XX

### Fixed
- 🐛 Fixed decorator bugs in monitoring.py (timed_operation and cached decorators)
- 🔧 Fixed BaseRepository initialization with proper logger and metrics
- ✅ Resolved TypeError in CLI commands

### Changed
- 📝 Updated documentation with correct migration examples
- 🔄 Improved decorator implementation to work without arguments

## [1.0.0] - 2024-01-XX

### Added
- 🚀 Advanced JSON-based ORM with async support
- 🔍 Query Builder with operators (gt, lt, like, in, etc.)
- ⚡ Automatic indexing and query caching
- 🔗 Foreign keys and relationships support
- 📊 Aggregation functions (count, sum, avg, min, max)
- 🛡️ Schema validation and unique constraints
- 📈 Performance monitoring and metrics
- 🔧 CLI commands for migrations with automatic model discovery
- 🗂️ Auto-discovery of models from project files (no manual registration needed)
- 🔄 Automatic table creation and schema updates
- 💾 Backup/restore functionality
- 🔄 Middleware support for logging and custom logic
- 📦 Data compression for production use
- 🏥 Health checks for monitoring
- 🎯 Pagination support for large datasets

### Features
- **Models**: Pydantic-based models with automatic discovery
- **Migrations**: Auto-discovery system - no manual model registration required
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
from jslorm import Database, BaseModel, BaseRepository

# Just define models - they're auto-discovered
class User(BaseModel):
    name: str
    email: str
    __table_name__ = "users"

# Initialize and auto-discover all models
db = Database("myapp")
await db.init_db()  # Finds all BaseModel classes automatically

# Or use CLI
# jslorm init
```