# Release v1.0.1
## Update Library in Project

```bash
# Update from git
pip install --upgrade git+https://github.com/dottenv/jslorm.git@v1.0.1

# Or force reinstall
pip uninstall jslorm
pip install git+https://github.com/dottenv/jslorm.git@v1.0.1
```

## What's Fixed

- ✅ Fixed `@timed_operation` decorator TypeError
- ✅ Fixed `@cached` decorator implementation  
- ✅ Added proper logger and metrics to BaseRepository
- ✅ Updated documentation with correct examples
