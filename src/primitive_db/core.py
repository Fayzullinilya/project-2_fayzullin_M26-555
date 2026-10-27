from primitive_db import constants, parser


def _is_valid_name(name :str) -> bool:
    """Проверяет корректность имени таблицы или колонки"""
    if not name:
        return False

    # Имя должно состоять только из букв, цифр и подчёркивания,
    # и начинаться с буквы или подчёркивания
    return(
        (all(('A' <= char <= 'Z') or
             ('a' <= char <= 'z') or 
             ('0' <= char <= '9') or
             (char == '_') 
             for char in name)
            and (name[0].isalpha() or name[0] == '_')
        )
    )

def create_table(metadata :dict , table_name :str, columns :list) -> dict:
    """
    Создает таблицу в метаданных.

    Параметры:
        metadata (dict): Словарь метаданных базы данных.
        table_name (str): Имя создаваемой таблицы.
        columns (list[tuple[str,str]]): Список кортежей ('имя', 'тип'),
        например [('id' ,'int'), ('title' ,'text'), ('release_year', 'int')].

    Правила именования:
        - Имена таблиц и колонок обрабатываются без учёта регистра 
          (например, 'Id', 'ID', 'id' считаются одним и тем же именем).
        - Названия типов всегда приводятся к нижнему регистру   
        - Колонка 'id' (тип 'int') добавляется автоматически. Если пользователь 
          передаёт колонку с именем 'id' в любом регистре, она игнорируется.
        - Если наименовани колонок дублируются (в любом регистре) добавляется
          только первая по порядку следования, остальные игнорируются.
        - Для создании таблицы требуется как минимум одна пользовательская колонка
          Минимальная таблица может содержать 2 колонки: id + колонка пользователя.

    Выполняет следующие шаги:
        - Проверяет, существует ли таблица с указанным именем.
        - Валидирует имя таблицы (допустимые символы, зарезервированные слова).
        - Проверяет имена кольнок на дубликаты
        - Проверяет корректность типов данных колонок.
        - Валидирует имена колонок (допустимые символы, зарезервированные слова).
        - Добавляет описание таблицы в метаданные.

    Возвращает:
        dict: Обновлённые метаданные с добавленной таблицей.

    Вызывает:
        ValueError: Если имя таблицы или колонок некорректно, либо таблица
                    уже существует.
    """

    # Проверка: имя таблицы не содержит запрещенные символы и не начинается с цифры
    if not _is_valid_name(table_name):
        raise ValueError(
            f'Неверное имя таблицы "{table_name}". Имя может содержать только '
             'символы: "A-Z", "a-z", "0-9", "_" и не может начинаться с цифры.'
        )

    # Проверка: имя таблицы не входит в список зарезервированных слов 
    if table_name.lower() in constants.RESERVED_WORDS_LIST:
        raise ValueError(
            f'"{table_name}" является зарезервированным словом и не может быть '
             'использовано в качестве имени таблицы.'
        )    

    # Проверка: таблица уже существует
    tables = metadata.get('tables', [])
    for table in tables:
        if table.get("name").lower() == table_name.lower():
            raise ValueError(f'Таблица {table_name} уже существует.')

    new_columns = [{'name':'id', 'type':'int'}] # Автоматическое добаление id
    added_columns = ['id'] # список добавленных колонок для поиска дубликатов
    
    for column in columns:    

        # Провера формата
        if not isinstance(column, tuple) or len(column) != 2:
            raise ValueError(
                f'Элемент списка колонок {column} должен быть кортежем из'
                 'двух значений (имя, тип).'
            )

        col_name,col_type = column
        
        # типы данных записываются в нижнем регистре
        col_type = col_type.lower()

        # Колонка "id:int" добавлена автоматически. Пропускаем 
        if col_name.lower() == 'id':
            continue

        # Пропуск дубликатов
        if col_name.lower() in added_columns:
            continue
        added_columns.append(col_name.lower())

        # Проверка: имя колонки не содержит запрещенные символы и не начинается с цифры
        if not _is_valid_name(col_name):
            raise ValueError(
                f'Неверное имя колонки "{col_name}". Имя может содержать только '
                 'символы: "A-Z", "a-z", "0-9", "_" и не может начинаться с цифры.'
            )
  
        # Проверка: имя колонки не входит в список зарезервированных слов 
        if col_name.lower() in constants.RESERVED_WORDS_LIST:
            raise ValueError(
                f'"{col_name}" является зарезервированным словом и не может быть '
                 'использовано в качестве имени колонки.'
            )

        # Проверка: тип данных соответствует допустимым
        if col_type.lower() not in constants.VALID_TYPE_LIST:
            raise ValueError(
                f'Недопустимый тип данных {col_type} для колонки {col_name}. '
                f'Допустимые типы данных: {constants.VALID_TYPE_LIST}.'
            )

        # Добавляем валидированную колонку в список новых колонок 
        new_column = {'name':col_name, 'type':col_type}
        new_columns.append(new_column)

    # Проверка: небыло добавлено ниодной польовательской колонки
    if len(new_columns) == 1:
        raise ValueError('Недостаточно колонок для создания таблицы.')

    # Добавляем новую таблицу
    new_table = {"name":table_name, "columns":new_columns}
    tables.append(new_table)
    metadata['tables'] = tables
    return metadata

def drop_table(metadata :dict, table_name :str) -> dict:
    """
    Удаляет таблицу из метаданных.
    Параметры:
        metadata (dict): Словарь метаданных базы данных.
        table_name (str): Имя Удаляемой таблицы.
    Возвращает:
        dict: Обновлённые метаданные без удаленной таблицы.
    Вызывает:
        ValueError: Если указанная таблица не существует.
    """
    tables = metadata.get('tables', [])

    for i, table in enumerate(tables):
        if table.get('name').lower() == table_name.lower():
            tables.pop(i)
            metadata['tables'] = tables
            return metadata

    raise ValueError(f'Таблицы {table_name} не существует.')    

def list_tables(metadata :dict) -> list:
    """
    Параметры: metadata (dict): Словарь метаданных базы данных.
    Возвращает: list: Список таблиц из метаданных.
    """
    tables = metadata.get('tables', [])
    return [table.get('name','') for table in tables]

def insert(metadata :dict, table_name :str, table_data :list, values :list) -> dict:
    """
    Добавляет одну запись в таблицу.

    Параметры:
        metadata (dict): Словарь метаданных базы данных.
        table_name (str): Имя таблицы в которую необходимо добавить запись.
        table_data (list[dict]): Данные таблицы. Параметр не указан в тексте
            задания, но он здесь нужен, что бы исключить необходимость вызывать
            utils.load_table_data(), поскольку это нарушит принятую структуру.
        values (list): Список значений, например ["Sergei", 28, true].

    Правила:
        - Все колонки таблицы считаются обязательными.
        - ID генерируется автоматически - max(IDs).
        - Значения типв bool могут передаваться в любом регистре, а так же
          в виде "0"/"1"

        - Считаем, что следующие условия гарантированы процедурой создания
          таблицы create_table (проверки не выполняются):
          - первая колонка называется 'id';
          - в таблице есть как минимум одна колонка кроме 'id';
          - типы колонок только int, str, bool в нижнем регистре;
          - колонка 'id' содержит только целые числа (гарантия insert).

    Выполняет следующие шаги:
        - Проверяет, существует ли таблица с указанным именем в метаданных.
        - Проверяет, что количество переданных значений соответствует 
          количеству столбцов (минус ID).
        - Валидирует типы данных для каждого значения в соответствии со
          схемой в метаданных.
        - Генерирует новый ID.
        - Добавляет новую запись (в виде словаря) в данные таблицы.

    Возвращает:
        dict: Данные таблицы с добавленной новой строкой.

    Вызывает:
        ValueError: Если таблица не существует, не совпадает количество столбцев
                    или неверный тип даных. 
    """

    tables = metadata.get('tables', [])

    if table_name not in tables:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    table = tables[table_name]
    columns = table['columns']

    # Проверка количества значений (без id)
    if len(values) != len(columns) - 1:
        raise ValueError(
            f"Ожидается {len(columns) - 1} значений (без id), получено {len(values)}."
        )

    # Расчёт следующего ID
    ids = [row['id'] for row in table_data]
    max_id = max(ids) if ids else 0
    next_id = max_id + 1

    # Сборка новой строки
    new_row = {'id': next_id}

    for i, col in enumerate(columns[1:], start=0):
        col_name = col.get('name')
        col_type = col.get('type')
        raw_value = values[i]

        # Проверка типов данных
        match col_type:
            case 'int':
                try:
                    value = int(raw_value)
                except (ValueError, TypeError):
                    raise ValueError(
                        f'Для колонки "{col_name}" ожидался int, '
                        f'получено: {raw_value}'
                    )
            case 'bool':
                if raw_value.lower() == "true" or raw_value == '1':
                    value = True
                elif raw_value.lower() == "false" or raw_value == '0':
                    value = False
                else:
                    raise ValueError(
                        f'Для колонки "{col_name}" ожидался bool (true/false), '
                        f'получено: {raw_value}'
                    )
            case _:
                # Все остальное - это str
                value = raw_value

        new_row[col_name] = value

    return table_data + [new_row]

def select(table_data: list, where_clause: str = None) -> list:
    """
    Возвращает отфильтрованный список строк (dict).
    """
    filters = parser.parse_where(where_clause)

    if not filters:
        # Без фильтра возвращаем все строки
        return [row.copy() for row in table_data]

    def matches(row: dict) -> bool:
        for col, expected in filters.items():
            if col not in row:
                return False
            if row[col] != expected:
                return False
        return True

    return [row.copy() for row in table_data if matches(row)]


