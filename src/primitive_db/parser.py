def parse_string(s: str) -> list:
    """
    Разбивает строку значений по запятым, игнорируя запятые внутри кавычек.
    Поддерживает одинарные и двойные кавычки.
    
    Пример: '"Sergei Ivanov", 28, true' -> ['Sergei Ivanov', '28', 'true']
    """
    result = []
    current = []
    in_quote = None  # None, '"' или "'"

    for ch in s:
        if in_quote is None:
            # Вне кавычек
            if ch in ('"', "'"):
                # Нашли открывающую кавычку
                in_quote = ch
            elif ch == ",":
                # Запятая вне кавычек — конец элемента
                result.append("".join(current).strip())
                current = []
            else:
                # Обычный символ
                current.append(ch)
        else:
            # Внутри кавычек: всё подряд идёт в current, пока не встретим закрывающую
            if ch == in_quote:
                # Закрыли кавычки
                in_quote = None
            else:
                # Любой другой символ внутри кавычек (включая запятые!)
                current.append(ch)

    # Добавляем последний элемент
    if current:
        result.append("".join(current).strip())

    return result

def parse_value(val_str: str):
    val_str = val_str.strip()

    # bool
    if val_str.lower() == 'true':
        return True
    if val_str.lower() == 'false':
        return False

    # int
    if val_str.lstrip('-').isdigit():
        return int(val_str)

    # str — только если в кавычках
    if (val_str.startswith('"') and val_str.endswith('"')) or \
       (val_str.startswith("'") and val_str.endswith("'")):
        return val_str[1:-1]

    raise ValueError(f'Не удалось распарсить значение: {val_str}')


def parse_where(where_str: str) -> dict:
    """
    Парсит строку where вида:
      "age = 28"
      "name = 'Sergei'"
      "age = 28, name = 'Sergei'"
    
    Возвращает словарь фильтров.
    Строковые значения должны быть в кавычках.
    """
    if not where_str or not where_str.strip():
        return {}

    where_str = where_str.strip()
    result = {}

    parts = parse_string(where_str)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        eq_index = part.find('=')
        if eq_index == -1:
            raise ValueError(f'В условии нет "=": {part}')

        key = part[:eq_index].strip()
        val_raw = part[eq_index + 1:].strip()

        if not key or not (key[0].isalpha() or key[0] == '_'):
            raise ValueError(f'Недопустимое имя колонки: {key}')
        if any(not (c.isalnum() or c == '_') for c in key):
            raise ValueError(f'Недопустимые символы в имени колонки: {key}')

        val = parse_value(val_raw)
        result[key] = val

    return result
