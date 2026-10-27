import json


def load_metadata(filepath :str) -> dict:
    """
    Загружает метаданные базы данных из JSON-файла.

    Параметры:
        filepath: путь к файлу метаданных в формате JSON.

    Возвращает:
        dict: содержимое файла как словарь. Если файл не найден возвращается 
              пустой словарь {}.

    Вызывает:
        RuntimeError: если файл повреждён (невалидный JSON), нет доступа
                      к файлу или произошла ошибка чтения. Работа приложения
                      должна быть остановлена, что бы избежать потерии данных.
                      (не перезаписывать существующие данные пустым справочником).
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            db_meta = json.load(f)
            return db_meta 
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        raise RuntimeError(
            'Файл метаданных повреждён: проверьте или удалите его, '
            'чтобы начать с новой базы.'
        )
    except PermissionError:
        raise RuntimeError(
            'Нет доступа к файлу метаданных: проверьте права, '
            'или удалите файл для создания новой базы.'
        )
    except OSError as e:
        raise RuntimeError(
            f'Ошибка чтения файла метаданных. {e}',
        )

def save_metadata(filepath :str, data :dict) -> None:   
    """
    Сохраняет метаданные базы данных в JSON-файл.

    Параметры:
        filepath: путь к файлу метаданных в формате JSON.
        data: словарь с метаданными для сохранения.

    Вызывает:
        RuntimeError: если данные не сериализуются в JSON, нет прав на запись
                      или произошла ошибка записи. Сохранение метаданных не 
                      происходит. Работа приложения должна быть остановлена,
                      что бы избежать потерии данных.
    """    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except TypeError:
        raise RuntimeError(
            'Не удалось сериализовать данные в JSON. '
            'Изменения не сохранились'
        )
    except PermissionError:
        raise RuntimeError(
            'Нет прав на запись файла метаданных. '
            'Изменения не сохранились'
        )
    except OSError as e:
        raise RuntimeError(
            f'Ошибка записи файла метаданных. {e}',
        )