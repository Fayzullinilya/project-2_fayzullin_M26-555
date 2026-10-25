import re

VALID_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
VALID_TYPE_LIST = {'int', 'str', 'bool'}
RESERVED_WORDS_LIST = {
    'order', 'group', 'select', 'insert', 'update', 'delete', 'from',
    'where', 'and', 'or', 'not', 'null', 'true', 'false', 'count',
    'sum', 'avg', 'min', 'max', 'date', 'time', 'timestamp'
}

def create_table(metadata, table_name, columns):
    
    if not VALID_NAME_PATTERN.match(table_name):
        print(f'Имя таблицы "{table_name}" содержит недопустимые символы. Допустимые',
              'символы: "A-Z", "a-z", "0-9", "_".')
        return
    if table_name[0].isdigit():
        print(f'Имя таблицы "{table_name}" не может начинаться с цифры. Допустимые',
              'символы: "A-Z", "a-z", "_".')
        return
    if table_name.lower() in RESERVED_WORDS_LIST:
        print(f'В качестве имени таблицы {table_name} нельзя использовать',
              'зарезервированные слова: {RESERVED_WORDS_LIST}')
        return

    tables = metadata.get('tables', [])
    is_exist = False
    for table in tables:
        if table_name == table['name']:
            is_exist = True
            break
    if is_exist:
        print(f'Таблица {table_name} уже существует')
        return
    
    new_columns = []
    for col in columns:
        if ':' not in col:
            print(f'Неверный формат колонки "{col}". Введите: [create_table',
                  '<имя_таблицы> <столбец1:тип> <столбец2:тип> ...].')
            return

        name, type = col.split(':')

        if not VALID_NAME_PATTERN.match(name):
            print(f'Имя колонки "{name}" содержит недопустимые символы. Допустимые',
                  'символы: "A-Z", "a-z", "0-9", "_".')
            return
        if name[0].isdigit():
            print(f'Имя колонки "{name}" не может начинаться с цифры. Допустимые',
                  'символы: "A-Z", "a-z", "_".')
            return
        if name.lower() in RESERVED_WORDS_LIST:
            print(f'В качестве имени колонки {name} нельзя использовать',
                  'зарезервированные слова: {RESERVED_WORDS_LIST}')
            return
        if type not in VALID_TYPE_LIST:
            print(f'Недопустимый тип данных {type} для колонки {name}. Допустимые типы',
                  'данных: {VALID_TYPE_LIST}')
            return                        
        new_column = {'name':name, 'type':type}
        new_columns.append(new_column)
    
    if 'id' not in new_columns:
        new_columns.insert(0,{'name':'id', 'type':'int'})    
    new_table = {"name":table_name, "columns":new_columns}
    
    tables.append(new_table)
    metadata['tables'] = tables
    print(f'Таблица {table_name} успешно создана со столбцами id:int,',
          f'{', '.join(columns)}.')
    return metadata

def drop_table(metadata, table_name):
    tables = metadata.get('tables', [])
    if len(tables) == 0:
        print('База данных не содержит таблиц')
        return

    i = 0
    is_exist = False
    for table in tables:
        if table_name == table['name']:
            is_exist = True
            table_position = i
            break
        i += 1

    if not is_exist:
        print(f'Таблицы {table_name} не существует')
        return
    metadata['tables'].pop(table_position)
    print(f'Таблица {table_name} удалена')
    return metadata

def list_tables(metadata):
    tables = metadata.get('tables', [])
    if len(tables) == 0:
        print('База данных не содержит таблиц')
        return

    for table in tables:
        print(f' - {table['name']}')





