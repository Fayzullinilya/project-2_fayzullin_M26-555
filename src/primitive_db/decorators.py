import time
from functools import wraps


def handle_errors(func) -> None:
    """
    Декоратор для обработки ошибок.
    Перехватывает:
      - KeyError: несуществующая таблица/колонка
      - ValueError: ошибки валидации типов, форматов, кавычек и т.п.
      - FileNotFoundError: проблемы с файлом БД

    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            print(f'Ошибка метаданных: {str(e).strip("'\"")}')
        except ValueError as e:
            print(f'Ошибка данных: {str(e).strip("'\"")}')
        except FileNotFoundError as e:
            print(f'Файл не найден: {str(e).strip("'\"")}')
        return None
    return wrapper

def confirm_action(action_name: str):
    """
    Декоратор для запроса подтверждения перед выполнением опасной операции.
    Если пользователь вводит 'y' или 'Y' — выполняется декорируемая функция.
    В остальных случаях операция отменяется.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = input('Вы уверены, что хотите выполнить '
                             f'"{action_name}"? [y/n]: ')
            if response.strip().lower() != 'y':
                print(f'Операция "{action_name}" отменена.')
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator

def log_time(func):
    """Декоратор для замера времени выполнения функции"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        elapsed_time = time.monotonic() - start_time
        print(f"Функция {func.__name__} выполнилась за {elapsed_time:.3f} секунд")
        return result
    return wrapper

def create_cacher():
    """
    Применени замыкания для кэширования запроса. 
    Проверяет, есть ли результат в кэше по ключу. Если есть — возвращает его.
    Если нет — вызываетфункцию
    """
    cache = {}

    def cache_result(key, func):
        if key in cache:
            return cache[key]
        result = func()
        cache[key] = result
        return result

    def clear():
        cache.clear()

    return cache_result, clear