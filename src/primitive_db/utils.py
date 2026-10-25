import json
import pathlib


def load_metadata(filepath):
    p = pathlib.Path(filepath)
    try:
        with p.open("r", encoding="utf-8") as f:
            db_meta = json.load(f)
            return db_meta 
    except FileNotFoundError:
        print(f'Файл {filepath} не найден. Создана новая БД.')
        return {}
    except json.JSONDecodeError:
        print(f'Ошибка при чтении файла {filepath}. Создана новая БД.')
        return {}
    
def save_metadata(filepath, data):
    p = pathlib.Path(filepath)    
    
    try:
        with p.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    except TypeError:
        print(f'Не удалось сериализовать данные в JSON. Файл {filepath} не обновлен.')
        
    except (OSError, PermissionError):
        print(f'Ошибка записи файла {filepath}.')