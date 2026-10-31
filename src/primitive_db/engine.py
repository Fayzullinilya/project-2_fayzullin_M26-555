import shlex

import prettytable as pt
import prompt

from primitive_db import constants, core, parser, utils


def handle_create(db_meta: dict, args: list[str]) -> dict:
    """
    Обработчик команды create_table.

    Параметры:
        db_meta (dict): Словарь метаданных базы данных.
        args (list[str]): Список аргументов командной строки.

    Выполняет:
        - Проверку наличия всех необходимых параметров в командной строке;
        - Парсинг командной строки на имя таблицы и список колонок в формате
          списка кортежей (имя, тип);
        - Вызов процедуры создания таблицы из модуля core;
        - Вызов процедуры сохранения метаданных из модуля utils;
        - Вывод сообщения о успешном создании таблицы в консоль.

    Возвращает:
        dict: Обновлённые метаданные с добавленной таблицей.

    Вызывает:
        ValueError: Если командная строка задана неверно.
    """

    if len(args) < 3:
        raise ValueError(
            'Неверный формат команды. Используйте: '
            'create_table <имя_таблицы> <столбец1:тип> [столбец2:тип ...]'
        )

    table_name = args[1]
    raw_columns = args[2:]

    columns = parser.parse_columns(raw_columns)
    db_meta_new = core.create_table(db_meta, table_name, columns)
    utils.save_metadata(constants.DB_META_JSON, db_meta_new)

    columns_str = ', '.join(f'"{name}":{typ}' for name, typ in columns)
    print(f'Таблица "{table_name}" успешно создана с колонками: {columns_str}.')

    return db_meta_new

def handle_drop(db_meta :dict, args :list[str]) -> dict:
    """
    Обработчик команды drop_table.

    Параметры:
        db_meta (dict): Словарь метаданных базы данных.
        args (list[str]): Список аргументов командной строки.

    Выполняет:
        - Проверку наличие всех необходимых параметров в командной строке;
        - Парсинг командной строки - имя таблицы;
        - Вызов процедуры удаления таблицы из модуля core;
        - Вызов процедуры сохранения метаданных из модуля utils;
        - Вывод сообщения о успешном удалении таблицы в консоль.

    Возвращает:
        dict: Обновлённые метаданные без удаленной таблицы.

    Вызывает:
        ValueError: Если командная строка задана неверно.
    """

    if len(args) < 2:
        raise ValueError(
            'Неверный формат команды. Используйте: '
            'drop_table <имя_таблицы>'
        )
    table_name = args[1]
    db_meta_new = core.drop_table(db_meta, table_name)
    utils.save_metadata(constants.DB_META_JSON, db_meta_new)

    print(f'Таблица "{table_name}" успешно удалена.')
    
    return db_meta_new

def handle_list(db_meta :dict) -> None:
    """Обработчик команды list_tables. Выводит список всех таблиц в консоль."""
    tables_list = core.list_tables(db_meta)
    if tables_list:
        print('\n'.join(f' - {name}' for name in tables_list))
    else:
        print('База данных не содержит таблиц.')

def handle_insert(db_meta :dict, args :list[str]) -> None:
    """
    Обработчик команды insert.

    Параметры:
        db_meta (dict): Словарь метаданных базы данных.
        args (list[str]): Список аргументов командной строки.

    Выполняет:
        - Проверку формата командной строки (наличие ключевых слов into/values,
          количества аргументов);
        - Парсинг командной строки на имя таблицы и список значений;
        - Парсинг значений из скобок игнорируя запятые внутри кавычек;
        - Загрузку данных таблицы через utils.load_table_data;
        - Вызов core.insert для валидации и добавления строки;
        - Сохранение обновлённых данных через utils.save_table_data;
        - Вывод сообщения об успешном добавлении.

    Вызывает:
        ValueError: При неверном формате команды, отсутствии значений или ошибках
                    валидации в core.
    """
    if (len(args) < 5 or
        args[1].lower() != 'into' or 
        args[3].lower() != 'values'
    ):
        raise ValueError(
            'Неверный формат команды. Используйте: '
            'insert into <имя_таблицы> values (<str>, <int>, <bool>, ...)'
        )
    
    table_name = args[2]

    raw_values_str = ' '.join(args[4:])
    # Проверяем, что есть скобки
    if (not raw_values_str.startswith('(') or
        not raw_values_str.endswith(')')
    ):
        raise ValueError(
            'Неверный формат команды. Ожидалось: '
            'insert into <имя_таблицы> values (...)'
        )
    inner = raw_values_str[1:-1].strip()
    if not inner:
        raise ValueError(
            'Список значений пуст. Укажите хотя бы одно значение в скобках.'
        )

    values = parser.parse_values(inner)
    current_rows = utils.load_table_data(table_name)
    updated_rows, new_id = core.insert(db_meta, table_name,
                               current_rows, values)
    utils.save_table_data(table_name, updated_rows)

    print(f'Строка c id = {new_id} успешно добавлена в таблицу "{table_name}".')

def handle_select(db_meta :dict, args :list[str]) -> None:
    """
    Обработчик команды select.

    Параметры:
        db_meta (dict): Словарь метаданных базы данных.
        args (list[str]): Список аргументов командной строки.

    Выполняет:
        - Проверку формата команды (наличие ключевых слов select/from,
          минимального числа аргументов);
        - Поиск позиции 'where' и извлечение условия фильтрации;
        - Парсинг условия WHERE (если указано) с помощью parser.parse_where;
        - Загрузку данных через utils.load_table_data;
        - Вызов core.select для применения фильтра;
        - Форматирование и вывод результата через PrettyTable;

    Вызывает:
        ValueError: При неверном формате команды, отсутствии условия после where,
                    либо если таблица не найдена в метаданных.
    """

    if (len(args) < 3 or args[1].lower() != 'from'):
        raise ValueError(
            'Неверный формат команды. Используйте: '
            'select from <имя_таблицы> [where <столбец> = <значение>]'
        )

    table_name = args[2]

    where_index = None
    for i, word in enumerate(args):
        if word.lower() == 'where':
            where_index = i
            break

    where_string = None
    if where_index is not None:
        condition_parts = args[where_index + 1:]
        if not condition_parts:
            raise ValueError('Указано where, но нет условия.')
        where_string = " ".join(condition_parts)

    columns = core.get_columns(db_meta,table_name)
    if columns is None:
        raise ValueError(f'Таблица "{table_name}" не найдена в метаданных.')

    where_clause = parser.parse_where(where_string)
    table_data = utils.load_table_data(table_name)
    selected_data = core.select(table_data,where_clause)

    formatted_data = pt.PrettyTable()
    formatted_data.field_names = columns
    for row in selected_data:
        formatted_data.add_row([row.get(c) for c in columns])

    print(formatted_data)

def handle_update(db_meta :dict, args :list[str]) -> None:
    if len(args) < 4 or args[2].lower() != 'set':
        raise ValueError(
            'Неверный формат команды. Используйте: '
            'update <имя_таблицы> set <столбец> = <значение> [where <условие>]'
        )

    table_name = args[1]

    where_index = None
    for i, word in enumerate(args):
        if word.lower() == 'where':
            where_index = i
            break

    if where_index is not None:
        set_parts = args[3:where_index]
        where_parts = args[where_index + 1:]
        
        if not set_parts:
            raise ValueError(
                'Указано set, но нет присваивания (столбец = значение).'
         )
        if not where_parts:
            raise ValueError('Указано where, но нет условия.')
        set_string = " ".join(set_parts)
        where_string = " ".join(where_parts)
    else:
        set_parts = args[3:]
        if not set_parts:
            raise ValueError(
                'Указано set, но нет присваивания (столбец = значение).'
            )
        set_string = " ".join(set_parts)
        where_string = None

    set_clause = parser.parse_set(set_string)
    where_clause = parser.parse_where(where_string)

    current_rows = utils.load_table_data(table_name)
    updated_rows = core.update(db_meta, table_name, current_rows,
                               set_clause, where_clause)
    utils.save_table_data(table_name, updated_rows)
                    
    print(f'Записи в таблице "{table_name}" успешно обновлены.')

def handle_delete(args :str) -> None:
    if len(args) < 3 or args[1].lower() != 'from':
        raise ValueError(
            'Используйте: delete from <имя_таблицы> [where <столбец> = <значение>]'
        )
    table_name = args[2]

    where_index = None
    for i, word in enumerate(args):
        if word.lower() == 'where':
            where_index = i
            break

    if where_index is not None:
        condition_parts = args[where_index + 1:]
        if not condition_parts:
            raise ValueError('Указано where, но нет условия.')
        where_string = " ".join(condition_parts)
    else:
        raise ValueError(
            'Для delete обязательно условие where '
            '(защита от случайного удаления всех строк).'
        )
    
    where_clause = parser.parse_where(where_string)
    table_data = utils.load_table_data(table_name)
    new_data = core.delete(table_data, where_clause)
    deleted_count = len(table_data) - len(new_data)

    if deleted_count == 0:
        raise ValueError(
            'По условию WHERE не найдено ни одной строки в '
            f'таблице "{table_name}". Записи не удалены.'
        )
    else:
        utils.save_table_data(table_name, new_data)
        print(
            f'Количество удаленных из таблицы "{table_name}" '
            f'записей - {deleted_count}.'
        )

def handle_info(db_meta :dict, args :str) -> None:
    if len(args) < 2:
        raise ValueError('Используйте: info <имя_таблицы>')
 
    table_name = args[1]

    table_meta = core.table_info(db_meta, table_name)
    if table_meta is None:
        raise ValueError('Таблица "{table_name}" не найдена в метаданных.')
    columns = table_meta["columns"]
    if not columns:
        raise ValueError(f'Таблица "{table_name}" найдена, но у неё нет колонок.')

    print(f"Информация о таблице: {table_meta['name']}")
    print("-" * 40)
    print(f"{'Колонка':<20} {'Тип':<10}")
    print("-" * 40)

    for col in columns:
        col_name = col.get("name", "<...>")
        col_type = col.get("type", "<...>")
        print(f"{col_name:<20} {col_type:<10}")

    print("-" * 40)
    print(f"Всего колонок: {len(columns)}")


def run() -> None:
    """
    Основной цикл:
        - Загружает метаданные
        - Принимает команду от пользоателя
        - Вызывает соответствующую процедуру-обработчик
        - Перехватывает исключения и выводит собщение об ошибке в консоль
    """

    try:
        db_meta = utils.load_metadata(constants.DB_META_JSON)
    except Exception as e:
        print(f'Критичесая ошибка: {e}')
        return

    while True:
        try:
            user_input = prompt.string('>>>Введите команду: ')
            args = shlex.split(user_input, posix=False)
            if len(args) == 0:
                continue
            
            command = args[0].lower()
            match command:
                case 'exit':
                    break
                case 'help':
                    print_help()
                case 'create_table':
                    db_meta = handle_create(db_meta, args)
                case 'drop_table':
                    db_meta = handle_drop(db_meta, args)
                case 'list_tables':
                    handle_list(db_meta)
                case 'insert':
                    handle_insert(db_meta, args)
                case 'select':
                    handle_select(db_meta, args)
                case 'update':
                    handle_update(db_meta, args)
                case 'delete':
                    handle_delete(args)
                case 'info':
                    handle_info(db_meta, args)
                case _:
                    print(
                        f'Неизвестная команда "{command}". '
                         'help - справочная информация.'
                    )

        except ValueError as e:
            print(f'Ошибка: {e}')

        except RuntimeError as e:
            print(f'Критичесая ошибка: {e}')
            break

        except Exception:
            print('Произошла неизвестная ошибка. Попробуйте повторить операцию.')

def print_help() -> None:
    """Выводит справочную информацию"""
   
    print("***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("\n***Операции с данными***")
    print("Функции:")
    print("<command> insert into <имя_таблицы> values (<значение1>, <значение2>, ...) "
          "- создать запись.")
    print("<command> select from <имя_таблицы> where <столбец> = <значение> - "
          "прочитать записи по условию.")
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print("<command> update <имя_таблицы> set <столбец1> = <новое_значение1> where "
          "<столбец_условия> = <значение_условия> - обновить запись.")
    print("<command> delete from <имя_таблицы> where <столбец> = <значение> - "
          "удалить запись.")
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")
