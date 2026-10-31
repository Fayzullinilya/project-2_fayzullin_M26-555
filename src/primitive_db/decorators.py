import time

def handle_errors(func) -> None:
    """
    Декоратор для обработки ошибок.
    Перехватывает:
      - KeyError: несуществующая таблица/колонка
      - ValueError: ошибки валидации типов, форматов, кавычек и т.п.
      - FileNotFoundError: проблемы с файлом БД

    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            print(f"Ошибка метаданных: {e}")
        except ValueError as e:
            print(f"Ошибка данных: {e}")
        except FileNotFoundError as e:
            print(f"Файл не найден: {e}")
        return None
    return wrapper

def confirm_action(action_name: str):
    """
    Декоратор для запроса подтверждения перед выполнением опасной операции.
    Если пользователь вводит 'y' или 'Y' — выполняется декорируемая функция.
    В остальных случаях операция отменяется.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            response = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ')
            if response.strip().lower() != 'y':
                print(f'Операция "{action_name}" отменена.')
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator

def log_time(func):
    """Декоратор для замера времени выполнения функции"""
    def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        elapsed_time = time.monotonic() - start
        print(f"Функция {func.__name__} выполнилась за {elapsed_time:.3f} секунд")
        return result
    return wrapper