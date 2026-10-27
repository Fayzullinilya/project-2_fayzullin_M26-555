import shlex

import prompt

import prettytable

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
                    if (len(command) < 5 or
                        command[1].lower() != 'into' or 
                        command[3].lower() != 'values'
                    ):
                        print(
                            'Используйте: [insert into <имя_таблицы>'
                            'values (<str>, <int>, <bool>, ...)]'
                        )
                        continue

                    table_name = command[2]

                    # Всё, что идёт после "values" — содержимое скобок
                    raw_values_str = ' '.join(command[4:])

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

                            # Если значение в кавычках (одинарных или двойных) — убираем их.
                            if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                                p = p[1:-1]

                            values.append(p)

                    current_rows = utils.load_table_data(table_name)
                    updated_rows = core.insert(db_meta, table_name, current_rows, values)
                    utils.save_table_data(table_name, updated_rows)
                    print(f"Строка успешно добавлена в таблицу '{table_name}'.")                 

                case 'select':
                    pass
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
   
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")
