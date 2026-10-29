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
    table = None
    for t in tables:
        if t.get("name").lower() == table_name.lower():
            table = t
            break

    if table is None:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    columns = table.get('columns',[])

    # Проверка количества значений (без id)
    if len(values) != len(columns) - 1:
        raise ValueError(
            f"Ожидается {len(columns) - 1} значений (без id), получено {len(values)}."
        )

    # Расчёт следующего ID
    ids = [row['id'] for row in table_data]
    if ids:
        next_id = max(ids) + 1
    else:
        next_id = 0

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
    Выполняет операцию SELECT для таблицы. Возвращает строки, удовлетворяющие
    условию WHERE. Если условие не указано, возвращаются все строки таблицы.

    Параметры:
        table_data (list): Список словарей, представляющих строки таблицы.
        where_clause (str): Условие фильтрации строк в формате пар «col = value».
                            Если не указано или равно None, возвращаются все строки.
                            Поддерживается только сравнение на равенство.
                            Пример: "id = 1" или "age = 18".

    Выполняет следующие шаги:
        - Если where_clause не передан — возвращает копию всех строк таблицы.
        - Парсит условие WHERE (ожидается формат: "col1 = val1, col2 = val2, ...").
        - Для каждой строки проверяет соответствие всем условиям из WHERE.
        - Собирает и возвращает список строк, которые удовлетворяют всем условиям.
        - Возвращает новую копию подходящих строк.

    Возвращает:
        Новый список словарей (копию подходящих строк таблицы). Если ни одна строка
        не удовлетворяет условию, возвращается пустой список. Исходный список
        `table_data` остаётся неизменным.

    Вызывает:
        ValueError: Если условие WHERE некорректно (например, отсутствует знак «=»,
                    невозможно распарсить значение и т.п.) или содержит
                    неподдерживаемый формат.
    """
    
    filters = parser.parse_where(where_clause)

    # Без фильтра возвращаем все строки
    if not filters:
        return [row.copy() for row in table_data]

    def matches(row: dict) -> bool:
        for col, expected in filters.items():
            if col not in row:
                return False
            if row[col] != expected:
                return False
        return True

    return [row.copy() for row in table_data if matches(row)]

def update(metadata: dict, table_name: str, table_data: list,
           set_clause: str, where_clause: str = None) -> list:
    """
    Выполняет операцию UPDATE для таблицы. Обновляет значения указанных колонок в
    строках, удовлетворяющих условию WHERE, с обязательной проверкой существования
    колонок и приведением типов значений согласно метаданным таблицы.

    Параметры:
    metadat (dict): Словарь метаданных базы данных.
    table_name (str): Имя таблицы, в которой выполняется обновление.
    table_data (list): Список словарей, представляющих строки таблицы.
    set_clause (str): Строка с присваиваниями для обновления. Формат:
                      "col1 = value1, col2 = value2". Значения могут быть в
                      кавычках (для строк), булевыми литералами или числами.
                      Пример: "age = 28, is_active = true, name = 'Ivan Ivanov'"
    where_clause (str): Условие фильтрации строк для обновления в формате пар 
                        "col = value". Если не указано или равно None, обновляются
                        все строки таблицы.
                        Пример: "id = 1" или "age = 18" (поддерживается только
                        равенство).
    
    Выполняет следующие шаги:
      - Ищет таблицу по имени (регистронезависимо).
      - Парсит предложение SET (ожидается формат: "col1 = val1, col2 = val2, ...").
      - Проверяет, что все указанные в SET колонки существуют в схеме таблицы.
      - Парсит условие WHERE (если передано) и находит совпадающие строки.
      - Если совпадений нет — возвращает копию исходной таблицы без изменений.
      - Для каждой совпадающей строки приводит значения к типам, указанным в метаданных
      - Возвращает новую копию таблицы с внесёнными изменениями.

    Возвращает:
        Dict: Новый список словарей (копию исходной таблицы) с обновлёнными значениями.
              Исходный список `table_data` остаётся неизменным.

    Вызывает:
        ValueError: Если таблица с указанным именем не найдена в метаданных, в SET
                    указана несуществующая колонка или значение не может быть
                    приведено к типу, указанному в метаданных.

    """
    tables = metadata.get('tables', [])
    table = None
    for t in tables:
        if t.get("name").lower() == table_name.lower():
            table = t
            break

    if table is None:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    columns = table.get("columns", [])
    columns_types = {col["name"]: col["type"] for col in table["columns"]}
    allowed_columns = {col.get("name") for col in columns if col.get("name")}

    set_values = parser.parse_where(set_clause)

    # Проверяем, что все колонки из SET существуют в схеме
    for col in set_values.keys():
        if col.lower() not in allowed_columns:
            raise ValueError(f'Колонка "{col}" не существует в таблице "{table_name}".')

    filters = parser.parse_where(where_clause)

    def matches(row :dict) -> bool:
        for col, expected in filters.items():
            if col not in row:
                return False
            if row[col] != expected:
                return False
        return True

    matched_indices = [i for i, row in enumerate(table_data) if matches(row)]
    if not matched_indices:
        return [row.copy() for row in table_data]

    new_table = [row.copy() for row in table_data]
    for idx in matched_indices:
        row = new_table[idx]
        for col_name, raw_value in set_values.items():
            expected_type = columns_types[col_name]
            match expected_type:
                case "int":
                    try:
                        value = int(raw_value)
                    except (ValueError, TypeError):
                        raise ValueError(
                            f'Для колонки "{col_name}" ожидался int, '
                            f'получено: "{raw_value}"'
                        )
                case "bool":
                    if isinstance(raw_value, bool):
                        value = raw_value
                    elif isinstance(raw_value, str):
                        v = raw_value.lower()
                        if v in ("true", "1"):
                            value = True
                        elif v in ("false", "0",):
                            value = False
                        else:
                            raise ValueError(
                                f'Для колонки "{col_name}" ожидался bool (true/false, '
                                f'1/0), получено: {raw_value}'
                            )
                    elif isinstance(raw_value, (int)):
                        value = bool(raw_value)
                    else:
                        raise ValueError(
                                f'Для колонки "{col_name}" ожидался bool (true/false, '
                                f'1/0), получено: {raw_value}'
                        )
                case "str":
                    value = str(raw_value)
                case _:
                    raise ValueError(
                        f'Не удалось преобразовать значение "{raw_value}" '
                        f'для колонки "{col_name}":"{expected_type}"' 
                    )
            row[col_name] = value

    return new_table

def delete(table_data :list, where_clause :str = None) -> list:
    """
    Удаляет строки, совпадающие с where_clause.
    Возвращает изменённый список table_data.
    Если совпадений нет — ничего не удаляет, список возвращается как есть.
    """
    # без условия не удаляем
    if not where_clause or not where_clause.strip():
        return table_data

    filters = parser.parse_where(where_clause)

    def matches(row):
        for col, expected in filters.items():
            if col not in row:
                return False
            if row[col] != expected:
                return False
        return True

    filtered = [row for row in table_data if not matches(row)]

    return filtered

def table_info(metadata: dict, table_name: str) -> dict:
    """
    Возвращает метаданные таблицы (name, columns) или None, если таблица не найдена.
    """
    tables = metadata.get('tables', [])
    for t in tables:
        t_name = t.get('name','')
        if str(t_name).lower() == table_name.lower():
            return {
                'name': t_name,
                'columns': t.get('columns', [])
            }
    return None