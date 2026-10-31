from primitive_db import constants


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

def _get_table(metadata :dict, table_name :str) -> dict | None:
    """
    Возвращает описание таблицы из метаданных по имени (без учёта регистра).
    Если таблица не найдена — возвращает None.
    """
    tables = metadata.get('tables', [])
    for table in tables:
        if table.get("name", '').lower() == table_name.lower():
            return table

def _validate_value(raw_value, col_name: str, col_type: str):
    """
    Валидирует и приводит значение к указаному типу (int, bool или str).
    Используется в insert и update.
    Вызывает ValueError если тип не совпадает с ожидаемым.
    """
    match col_type:
        case 'int':
            try:
                return int(raw_value)
            except (ValueError, TypeError):
                raise ValueError(
                    f'Для колонки "{col_name}" ожидался int, получено: {raw_value}'
                )
        case 'bool':
            raw_str = str(raw_value).strip().lower()
            if raw_str in ("true", "1"):
                return True
            elif raw_str in ("false", "0"):
                return False
            else:
                raise ValueError(
                    f'Для колонки "{col_name}" ожидался bool (true/false/1/0), '
                    f'получено: {raw_value}'
                )
        case _:
            # Всё остальное трактуем как str
            return str(raw_value)
        
def get_columns(metadata :dict, table_name :str) -> list | None:
    """
    Возвращает список колонок по имени таблицы
    Если таблица не найдена — возвращает None.
    """
    table = _get_table(metadata, table_name)
    if table:
        columns = table.get('columns',[])
        return [col.get('name','') for col in columns]

def create_table(metadata :dict , table_name :str,
                 columns :list[tuple[str,str]]) -> dict:
    """
    Создает таблицу в метаданных.

    Параметры:
        metadata (dict): Словарь метаданных базы данных.
        table_name (str): Имя создаваемой таблицы.
        columns (list[tuple[str,str]]): Список кортежей ('имя', 'тип'),
        например [('id' ,'int'), ('name' ,'text'), ('age', 'int')].

    Правила именования:
        - Имена таблиц и колонок обрабатываются без учёта регистра 
          (например, 'Id', 'ID', 'id' считаются одним и тем же именем).
        - Имена таблиц, колонок и названия типов хранятся в метаданных только
          в нижнем регистре.
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
    # Храним имена только в нижне регистре
    table_name = table_name.lower()
    
    # Проверка: имя таблицы не содержит запрещенные символы и не начинается с цифры
    if not _is_valid_name(table_name):
        raise ValueError(
            f'Неверное имя таблицы "{table_name}". Имя может содержать только '
             'символы: "A-Z", "a-z", "0-9", "_" и не может начинаться с цифры.'
        )

    # Проверка: имя таблицы не входит в список зарезервированных слов 
    if table_name in constants.RESERVED_WORDS_LIST:
        raise ValueError(
            f'"{table_name}" является зарезервированным словом и не может быть '
             'использовано в качестве имени таблицы.'
        )    

    tables = metadata.setdefault('tables', [])

    # Проверка: таблица уже существует
    for table in tables:
        if table.get("name", '') == table_name:
            raise ValueError(f'Таблица "{table_name}" уже существует.')

    new_columns = [{'name':'id', 'type':'int'}] # Автоматическое добаление id
    added_columns = ['id'] # список добавленных колонок для поиска дубликатов
    
    for column in columns:    

        # Провера формата
        if not isinstance(column, tuple) or len(column) != 2:
            raise ValueError(
                f'Элемент списка колонок "{column}" должен быть кортежем из'
                 'двух значений (имя, тип).'
            )

        col_name,col_type = column
        
        # имена колонок и типы данных хранятся в нижнем регистре
        col_name = col_name.lower()
        col_type = col_type.lower()

        # Колонка "id:int" добавлена автоматически. Пропускаем 
        if col_name == 'id':
            continue

        # Пропуск дубликатов
        if col_name in added_columns:
            continue
        added_columns.append(col_name)

        # Проверка: имя колонки не содержит запрещенные символы и не начинается с цифры
        if not _is_valid_name(col_name):
            raise ValueError(
                f'Неверное имя колонки "{col_name}". Имя может содержать только '
                 'символы: "A-Z", "a-z", "0-9", "_" и не может начинаться с цифры.'
            )
  
        # Проверка: имя колонки не входит в список зарезервированных слов 
        if col_name in constants.RESERVED_WORDS_LIST:
            raise ValueError(
                f'"{col_name}" является зарезервированным словом и не может быть '
                 'использовано в качестве имени колонки.'
            )

        # Проверка: тип данных соответствует допустимым
        if col_type not in constants.VALID_TYPE_LIST:
            raise ValueError(
                f'Недопустимый тип данных "{col_type}" для колонки "{col_name}". '
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
    table_name = table_name.lower()
    tables = metadata.setdefault('tables', [])

    for i, table in enumerate(tables):
        if table.get('name', '') == table_name:
            del tables[i]
            return metadata

    raise ValueError(f'Таблица "{table_name}" не найдена.')    

def list_tables(metadata :dict) -> list:
    """
    Возвращает список имён всех таблиц из метаданных.
    Если ключ 'tables' отсутствует или таблицы не найдены, возвращает пустой список.
    """
    tables = metadata.get('tables', [])
    return [table.get('name','') for table in tables]

def insert(metadata :dict, table_name :str,
           table_data :list[dict], values :list) -> tuple[list[dict], int]:
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
        - Значения типов bool могут передаваться в любом регистре, а так же
          в виде "0"/"1"
        - Считаем, что следующие условия гарантированы процедурой создания
          таблицы create_table (проверки не выполняются):
          - первая колонка называется 'id';
          - в таблице есть как минимум одна колонка кроме 'id';
          - типы колонок только int, str, bool в нижнем регистре;
          - названия таблиц и колонок хранятся в нижнем регистре
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
        tuple[list[dict], int]: (новый список строк, id добавленной записи).

    Вызывает:
        ValueError: Если таблица не существует, не совпадает количество столбцев
                    или неверный тип даных. 
    """

    table_name = table_name.lower()
    table = _get_table(metadata, table_name)
    if table is None:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    columns = table.get('columns',[])

    # Проверка количества значений (без id)
    if len(values) != len(columns) - 1:
        raise ValueError(
            f"Ожидается {len(columns) - 1} значений (без id), получено {len(values)}."
        )

    # Расчёт следующего ID
    ids = [row.get('id') for row in table_data]
    if not ids:
        next_id = 0
    else:
        next_id = max(ids) + 1

    # Сборка новой строки
    new_row = {'id': next_id}

    for i, col in enumerate(columns[1:], start=0):
        col_name = col.get('name')
        col_type = col.get('type')
        raw_value = values[i]

        # Проверка типов данных
        value = _validate_value(raw_value, col_name, col_type)
        
        new_row[col_name] = value

        new_table = [*table_data, new_row]
    return new_table, next_id

def select(table_data: list[dict], where_clause: dict = None) -> list[dict]:
    """
    Выполняет операцию SELECT для таблицы. Возвращает строки, удовлетворяющие
    условию WHERE. Если условие не указано, возвращаются все строки таблицы.

    Параметры:
        table_data (list): Список словарей, представляющих строки таблицы.
        where_clause (dict | None): Словарь условий фильтрации вида
                                    {col_name: expected_value}.
                                    Пример: {"age": 25, "status": "active"}.
                                    Если None — возвращаются все строки.

    Выполняет следующие шаги:
        - Проверяет существование таблицы в метаданных через _get_table;
        - Если where_clause не передан — возвращает копию всех строк таблицы;
        - Для каждой строки проверяет соответствие всем условиям из WHERE;
        - Собирает и возвращает список строк, которые удовлетворяют всем условиям;
        - Возвращает новую копию подходящих строк;

    Возвращает:
        Новый список словарей (копию подходящих строк таблицы). Если ни одна строка
        не удовлетворяет условию, возвращается пустой список.
    """

    # Без фильтра возвращаем все строки
    if not where_clause:
        return [row.copy() for row in table_data]

    def matches(row: dict) -> bool:
        for col, expected in where_clause.items():
            col = col.lower()
            if col not in row:
                return False
            if row[col] != expected:
                return False
        return True

    return [row.copy() for row in table_data if matches(row)]

def update(metadata: dict, table_name: str, table_data: list,
           set_clause: dict, where_clause: dict = None) -> list[dict]:
    """
    Выполняет операцию UPDATE для таблицы. Обновляет значения указанных колонок в
    строках, удовлетворяющих условию WHERE, с обязательной проверкой существования
    колонок и приведением типов значений согласно метаданным таблицы.

    Параметры:
    metadata (dict): Словарь метаданных базы данных.
    table_name (str): Имя таблицы, в которой выполняется обновление.
    table_data (list): Список словарей, представляющих строки таблицы.
    set_clause (dict): Словарь условий фильтрации вида
                       {col_name: set_value}.
                       Пример: {"age": 25, "status": "active"}.
    where_clause (dict | None): Словарь условий фильтрации вида
                                {col_name: expected_value}.
                                Пример: {"age": 25, "status": "active"}.
                                Если None — обновляются все строки.
    
    Выполняет следующие шаги:
      - Ищет таблицу по имени.
      - Проверяет, что все указанные в SET колонки существуют в схеме таблицы.
      - Если совпадений Where нет — возвращает копию исходной таблицы без изменений.
      - Для каждой совпадающей строки приводит значения к типам, указанным в метаданных
      - Возвращает новую копию таблицы с внесёнными изменениями.

    Возвращает:
        list[dict]: Новый список словарей (копию исходной таблицы) с обновлёнными
                    значениями.

    Вызывает:
        ValueError: Если таблица с указанным именем не найдена в метаданных, в SET
                    указана несуществующая колонка или значение не может быть
                    приведено к типу, указанному в метаданных.

    """

    table_name = table_name.lower()
    table = _get_table(metadata, table_name)
    if table is None:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    columns = table.get("columns", [])
    columns_types = {col["name"]: col["type"] for col in table["columns"]}
    allowed_columns = {col.get("name") for col in columns if col.get("name")}

    # Проверяем, что все колонки из SET существуют в схеме
    for col in set_clause.keys():
        if col.lower() not in allowed_columns:
            raise ValueError(f'Колонка "{col}" не существует в таблице "{table_name}".')

    def matches(row :dict) -> bool:
        if where_clause is None:
            return False
        for col, expected in where_clause.items():
            col = col.lower()    
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
        for col_name, raw_value in set_clause.items():
            col_name = col_name.lower()
            expected_type = columns_types[col_name]
            value = _validate_value(raw_value, col_name, expected_type)
            row[col_name] = value

    return new_table

def delete(table_data :list, where_clause :dict = None) -> list:
    """
    Удаляет строки, совпадающие с where_clause.
    Возвращает изменённый список table_data.
    Если совпадений нет — ничего не удаляет, список возвращается как есть.
    """
    # без условия не удаляем
    if not where_clause:
        return table_data

    def matches(row):
        for col, expected in where_clause.items():
            col = col.lower()
            if col not in row:
                return False
            if row[col] != expected:
                return False
        return True

    filtered = [row.copy() for row in table_data if not matches(row)]

    return filtered

def table_info(metadata: dict, table_name: str) -> dict:
    """
    Возвращает метаданные таблицы (name, columns) или None, если таблица не найдена.
    """

    table_name = table_name.lower()
    tables = metadata.get('tables', [])
    for t in tables:
        t_name = t.get('name', '')
        if t_name == table_name:
            return {
                'name': t_name,
                'columns': t.get('columns', [])
            }
    return None