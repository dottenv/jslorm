#!/bin/bash

# Скрипт для публикации в PyPI

echo "🚀 Publishing JSLORM to PyPI..."

# Проверяем что мы в правильной директории
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml not found. Run from project root."
    exit 1
fi

# Устанавливаем зависимости для публикации
echo "📦 Installing build dependencies..."
pip install --upgrade build twine

# Очищаем старые сборки
echo "🧹 Cleaning old builds..."
rm -rf dist/ build/ *.egg-info/

# Собираем пакет
echo "🔨 Building package..."
python -m build

# Проверяем пакет
echo "🔍 Checking package..."
python -m twine check dist/*

# Публикуем в Test PyPI (для тестирования)
echo "🧪 Publishing to Test PyPI..."
echo "Enter your Test PyPI credentials:"
python -m twine upload --repository testpypi dist/*

echo ""
echo "✅ Published to Test PyPI!"
echo "🔗 Check: https://test.pypi.org/project/jslorm/"
echo ""
echo "To install from Test PyPI:"
echo "pip install --index-url https://test.pypi.org/simple/ jslorm"
echo ""
echo "If everything works, publish to real PyPI:"
echo "python -m twine upload dist/*"