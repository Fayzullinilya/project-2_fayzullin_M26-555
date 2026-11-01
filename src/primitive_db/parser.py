def parse_columns(raw_cols: list[str]) -> list[tuple[str, str]]:
    """
    Рабирает список из описаний колонок "имя:тип" в список кортежей ('имя', 'тип')
    """
    columns = []
    for col in raw_cols:
        if col.count(':') != 1:
            raise ValueError(
                f'Описание колонки "{col}" должна содержать ровно одно '
                 'двоеточие (формат: имя:тип).'
            )
        name, typ = col.split(':', 1)
        if not name or not typ:
            raise ValueError(
                f'В рписании колонки "{col}" имя и тип не могут быть пустыми.'
            )
        columns.append((name, typ))
    return columns

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

def parse_values(raw_vals :str) -> list:
    """Парсит строку значений для insert игнорируя запятые внутри кавычек"""
    values = []
    if raw_vals:
        parts = parse_string(raw_vals)
        for p in parts:
            p = p.strip()
            if not p:
                continue

            # Если значение в кавычках — убираем их.
            if (p.startswith('"') and p.endswith('"')) or\
                (p.startswith("'") and p.endswith("'")):
                p = p[1:-1]

            values.append(p)
    return values    

def parse_value(val_str: str):
    """Парсит строковое представление значения в соответствующий Python-тип."""
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

    В текущей реализации парсеры where и set идентичны, поскольку
    where допускает только знак равенства.
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
            raise ValueError(f'В условии "{part}" отсутствует знак "=".')

        col_name = part[:eq_index].strip()
        val_raw = part[eq_index + 1:].strip()

        if not col_name:
            raise ValueError(f'Имя колонки не указано в условии "{part}".')

        value = parse_value(val_raw)
        result[col_name] = value

    return result

def parse_set(set_str: str) -> dict:
    """
    Парсит строку set вида:
      "age = 28"
      "name = 'Sergei'"
      "age = 28, name = 'Sergei'"
    
    Возвращает словарь присвоений.
    Строковые значения должны быть в кавычках.
    """

    if not set_str or not set_str.strip():
        return {}

    set_str = set_str.strip()
    result = {}

    parts = parse_string(set_str)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        eq_index = part.find('=')
        if eq_index == -1:
            raise ValueError(f'В присваивании "{part}" отсутствует знак "=".')

        col_name = part[:eq_index].strip()
        val_str = part[eq_index + 1:].strip()

        if not col_name:
            raise ValueError(f'Имя колонки не указано в присваивании "{part}".')

        # Приводим значение к типу
        value = parse_value(val_str)
        result[col_name] = value

    return result