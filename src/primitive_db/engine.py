import shlex

import prettytable as pt
import prompt

from primitive_db import constants, core, parser, utils


def parse_columns(raw_cols: list[str]) -> list[tuple[str, str]]:
    """Рабирает список из описаний колонок в список кортежей ('имя', 'тип')"""
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

def run() -> None:
    """
    Основной цикл:
        - Загружает метаданные
        - Принимает команду от пользоателя и проверяет ее на соответствие формату
        - Вызывает соответствующую процедуру из модуля core
        - Если выполнение успешно, сохраняет меаданные
        - Перехватывает все исключения генерируемые в модуле core
        - Выводит собщение о результате выполнения в консоль
    """

    db_meta = utils.load_metadata(constants.DB_META_JSON)

    while True:
        try:
            user_input = prompt.string('>>>Введите команду: ')
            args = shlex.split(user_input)
            if len(args) == 0:
                continue
            
            command = args[0].lower()
            match command:
                case 'exit':
                    break

                case 'help':
                    print_help()

                case 'create_table':
                    if len(args) < 3:
                        print(
                            'Отсутствуют yеобходимые параметры. Введите: [create_table '
                            '<имя_таблицы> <столбец1:тип> <столбец2:тип> ...].'
                        )
                        continue

                    table_name = args[1]
                    raw_columns = args[2:]
                    columns = parse_columns(raw_columns)
                    db_meta_new = core.create_table(db_meta, table_name, columns)
                    utils.save_metadata(constants.DB_META_JSON,db_meta_new)
                    db_meta = db_meta_new
                    
                    columns_str = ", ".join(f"{name}:{typ}" for name, typ in columns)
                    print(
                        f'Таблица {table_name} успешно создана с '
                        f'колонками {columns_str}.'
                    )
                
                case 'drop_table':
                    if len(args) < 2:
                        print(
                            'Отсутствует имя таблицы. Введите: '
                            '[drop_table <имя_таблицы>].'
                        )
                        continue
                    
                    table_name = args[1]
                    db_meta_new = core.drop_table(db_meta, table_name)
                    utils.save_metadata(constants.DB_META_JSON,db_meta_new)
                    db_meta = db_meta_new
                    print(f'Таблица {table_name} успешно удалена.')

                case 'list_tables':
                    tables_list = core.list_tables(db_meta)
                    if tables_list:
                        print('\n'.join(f' - {name}' for name in tables_list))
                    else:
                        print('База данных не содержит таблиц.')

                case 'insert':
                    if (len(args) < 5 or
                        args[1].lower() != 'into' or 
                        args[3].lower() != 'values'
                    ):
                        print(
                            'Используйте: [insert into <имя_таблицы> '
                            'values (<str>, <int>, <bool>, ...)]'
                        )
                        continue

                    table_name = args[2]

                    # Всё, что идёт после "values" — содержимое скобок
                    raw_values_str = ' '.join(args[4:])

                    # Проверяем, что есть скобки
                    if (not raw_values_str.startswith('(') or
                        not raw_values_str.endswith(')')
                    ):
                        print(
                            'Ошибка: ожидается формат: insert into <таблица>'
                            'values (<v1>, <v2>, ...)'
                        )
                        continue

                    inner = raw_values_str[1:-1].strip()
                    values = []

                    if inner:
                        parts = parser.parse_string(inner)
                        for p in parts:
                            p = p.strip()
                            if not p:
                                continue

                            # Если значение в кавычках — убираем их.
                            if (p.startswith('"') and p.endswith('"')) or\
                               (p.startswith("'") and p.endswith("'")):
                                p = p[1:-1]

                            values.append(p)

                    current_rows = utils.load_table_data(table_name)
                    updated_rows = core.insert(db_meta, table_name,
                                               current_rows, values)
                    utils.save_table_data(table_name, updated_rows)
                    print(f"Строка успешно добавлена в таблицу '{table_name}'.")
                    
                case 'select':
                    if (len(args) < 3 or
                        args[1].lower() != 'from'
                    ):
                        print(
                            'Используйте: [select from <имя_таблицы> '
                            'where <столбец> = <значение>]'
                        )
                        continue

                    table_name = args[2]
                    tables = db_meta.get('tables',[])
                    table = None
                    for t in tables:
                        if t.get("name",'').lower() == table_name.lower():
                            table = t
                            break

                    if table is None:
                        raise ValueError(f'Таблица "{table_name}" не существует.')

                    where_index = None
                    for i, word in enumerate(args):
                        if word.lower() == 'where':
                            where_index = i
                            break

                    if where_index is not None:
                        condition_parts = args[where_index + 1:]
                        if not condition_parts:
                            print('Указано where, но нет условия.')
                            return
                        where_clause = " ".join(condition_parts)
                    else:
                        where_clause = None

                    table_data = utils.load_table_data(table_name)
                    selected_data = core.select(table_data,where_clause)

                    formatted_data = pt.PrettyTable()
                    columns = [col.get('name','') for col in table.get('columns',[])]
                    formatted_data.field_names = columns
                    for row in selected_data:
                        formatted_data.add_row([row.get(c) for c in columns])

                    print(formatted_data)

                case 'update':
                    if len(args) < 4 or args[2].lower() != 'set':
                        print(
                            'Используйте: update <имя_таблицы> set <столбец> '
                            '= <значение> [where <условие>]'
                        )
                        continue

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
                            print(
                                'Указано set, но нет присваивания '
                                '(столбец = значение).'
                            )
                            continue    
                        if not where_parts:
                            print('Указано where, но нет условия.')
                            continue

                        set_clause = " ".join(set_parts)
                        where_clause = " ".join(where_parts)
                    else:
                        set_parts = args[3:]
                        if not set_parts:
                            print(
                                'Указано set, но нет присваивания '
                                '(столбец = значение).'
                            )
                            continue
                        set_clause = " ".join(set_parts)
                        where_clause = None

                    current_rows = utils.load_table_data(table_name)
                    updated_rows = core.update(db_meta, table_name, current_rows,
                                               set_clause, where_clause)
                    utils.save_table_data(table_name, updated_rows)
                    
                    print(f'Записи в таблице "{table_name}" успешно обновлены.')

                case 'delete':
                    if len(args) < 3 or args[1].lower() != 'from':
                        print(
                            'Используйте: delete from <имя_таблицы> '
                            '[where <столбец> = <значение>]'
                        )
                        continue

                    table_name = args[2]

                    where_index = None
                    for i, word in enumerate(args):
                        if word.lower() == 'where':
                            where_index = i
                            break

                    if where_index is not None:
                        condition_parts = args[where_index + 1:]
                        if not condition_parts:
                            print('Указано where, но нет условия.')
                            continue
                        where_clause = " ".join(condition_parts)
                    else:
                        print(
                            'Для delete обязательно условие where '
                            '(защита от случайного удаления всех строк).'
                        )
                        continue

                    table_data = utils.load_table_data(table_name)
                    new_data = core.delete(table_data, where_clause)
                    deleted_count = len(table_data) - len(new_data)

                    if deleted_count == 0:
                        print(
                             'По условию WHERE не найдено ни одной строки в '
                            f'таблице "{table_name}". Записи не удалены.'
                            )
                    else:
                        utils.save_table_data(table_name, new_data)
                        print(
                            f'Количество удвленных из таблицы "{table_name}" '
                            f'записей - {deleted_count}.'
                        )

                case 'info':
                    if len(args) < 2:
                        print('Используйте: info <имя_таблицы>')
                        continue

                    table_name = args[1]

                    table_meta = core.table_info(db_meta, table_name)
                    if table_meta is None:
                        print(f'Таблица "{table_name}" не найдена в метаданных.')
                        continue

                    columns = table_meta["columns"]
                    if not columns:
                        print(f'Таблица "{table_name}" найдена, но у неё нет колонок.')
                        continue

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
