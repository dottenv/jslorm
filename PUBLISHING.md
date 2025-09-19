# Публикация JSLORM в PyPI

## Подготовка

1. **Создайте аккаунт на PyPI:**
   - Основной: https://pypi.org/account/register/
   - Тестовый: https://test.pypi.org/account/register/

2. **Установите зависимости:**
```bash
pip install --upgrade build twine
```

## Пошаговая публикация

### 1. Проверьте версию
Обновите версию в `pyproject.toml`:
```toml
version = "1.0.1"  # Увеличьте версию
```

### 2. Соберите пакет
```bash
# Очистите старые сборки
rm -rf dist/ build/ *.egg-info/

# Соберите пакет
python -m build
```

### 3. Проверьте пакет
```bash
python -m twine check dist/*
```

### 4. Тестовая публикация
```bash
# Публикация в Test PyPI
python -m twine upload --repository testpypi dist/*

# Тестовая установка
pip install --index-url https://test.pypi.org/simple/ jslorm
```

### 5. Основная публикация
```bash
# Публикация в основной PyPI
python -m twine upload dist/*
```

## Автоматические скрипты

### Linux/Mac:
```bash
chmod +x publish.sh
./publish.sh
```

### Windows:
```cmd
publish.bat
```

## API токены (рекомендуется)

1. Создайте API токен на PyPI
2. Используйте вместо пароля:
```bash
python -m twine upload --username __token__ --password pypi-... dist/*
```

## Проверка публикации

После публикации проверьте:
- https://pypi.org/project/jslorm/
- Установка: `pip install jslorm`
- CLI: `jslorm --help`

## Обновление версий

Для новых версий:
1. Обновите версию в `pyproject.toml`
2. Обновите `CHANGELOG.md`
3. Создайте git tag: `git tag v1.0.1`
4. Повторите процесс публикации