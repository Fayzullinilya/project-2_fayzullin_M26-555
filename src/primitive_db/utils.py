import json
import pathlib


def load_metadata(filepath):
    p = pathlib.Path(filepath)
    try:
        with p.open("r", encoding="utf-8") as f:
            db_meta = json.load(f)
        if db_meta:
            return db_meta 
        else:
            print('Данные в файле {filepath} отсутствуют. Создана новая БД.')
            return {}
    except FileNotFoundError:
        print('Файл {filepath} не найден. Создана новая БД.')
        return {}
    except json.JSONDecodeError as e:
        print('Ошибка при чтении файла {filepath}. Создана новая БД.')
        return {}
    
def save_metadata(filepath, data):
    p = pathlib.Path(filepath)    
    
    try:
        with p.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    except TypeError as e:
        print('Не удалось сериализовать данные в JSON. Файл {filepath} не обновлен.')
        
    except (OSError, PermissionError) as e:
        print('Ошибка записи файла {filepath}.')