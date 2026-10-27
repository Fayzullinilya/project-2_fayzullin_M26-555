# Файл метаданных
DB_META_JSON = 'db_meta.json'

# Папка с данными таблиц
DB_DATA_PATH = 'data'

# Список допустимых типов колонок
VALID_TYPE_LIST = {'int', 'str', 'bool'}

# Список зарезервированных слов с которыми не могут совпадать наименования
# таблиц и колонок 
RESERVED_WORDS_LIST = {
    'order', 'group', 'select', 'insert', 'update', 'delete', 'from',
    'where', 'and', 'or', 'not', 'null', 'true', 'false', 'count',
    'sum', 'avg', 'min', 'max', 'date', 'time', 'timestamp'
}
