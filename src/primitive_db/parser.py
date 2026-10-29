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
            if ch in ('"', "'"):
                in_quote = ch
            elif ch == ",":
                result.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        else:
            if ch == in_quote:
                in_quote = None
            else:
                current.append(ch)

    if current:
        result.append("".join(current).strip())

    return result

def parse_value(val_str: str):
    """
    """
    val_str = val_str.strip()
    # bool
    if val_str.lower() == 'true':
        return True
    if val_str.lower() == 'false':
        return False

    # int
    if val_str.lstrip('-').isdigit():
        return int(val_str)

    # str
    return val_str

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

        val = parse_value(val_raw)
        result[key] = val

    return result

