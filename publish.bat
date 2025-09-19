@echo off

REM Скрипт для публикации в PyPI (Windows)

echo 🚀 Publishing JSLORM to PyPI...

REM Проверяем что мы в правильной директории
if not exist "pyproject.toml" (
    echo ❌ pyproject.toml not found. Run from project root.
    exit /b 1
)

REM Устанавливаем зависимости для публикации
echo 📦 Installing build dependencies...
pip install --upgrade build twine

REM Очищаем старые сборки
echo 🧹 Cleaning old builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
for /d %%i in (*.egg-info) do rmdir /s /q "%%i"

REM Собираем пакет
echo 🔨 Building package...
python -m build

REM Проверяем пакет
echo 🔍 Checking package...
python -m twine check dist/*

REM Публикуем в Test PyPI (для тестирования)
echo 🧪 Publishing to Test PyPI...
echo Enter your Test PyPI credentials:
python -m twine upload --repository testpypi dist/*

echo.
echo ✅ Published to Test PyPI!
echo 🔗 Check: https://test.pypi.org/project/jslorm/
echo.
echo To install from Test PyPI:
echo pip install --index-url https://test.pypi.org/simple/ jslorm
echo.
echo If everything works, publish to real PyPI:
echo python -m twine upload dist/*

pause