# Release v1.0.1

## Git Commands to Create Release

```bash
# Add all changes
git add .

# Commit changes
git commit -m "Release v1.0.1: Fix decorator bugs and improve documentation"

# Create and push tag
git tag -a v1.0.1 -m "Release v1.0.1: Fix decorator bugs"
git push origin main
git push origin v1.0.1

# Create GitHub release (optional)
gh release create v1.0.1 --title "v1.0.1" --notes "Fixed decorator bugs in monitoring system"
```

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