import prompt
import shlex
from primitive_db import core
from primitive_db import utils

DB_META_JSON = 'db_meta.json'

def run():

    db_meta = utils.load_metadata(DB_META_JSON)

    while True:
        user_input = prompt.string('>>>Введите команду: ')
        args = shlex.split(user_input)
        if len(args) == 0:
            continue
        
        match args[0]:
            case 'exit':
                break
            case 'help':
                print_help()
            case 'create_table':
                if len(args) < 2:
                    print('Отсутствует имя таблицы. Введите: [create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> ...]')
                    continue
                if len(args) < 3:
                    print('Отсутствует описание колонок. Введите: [create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> ...]')
                    continue
                db_meta_new = core.create_table(db_meta, args[1], args[2:])
                if db_meta_new:
                    utils.save_metadata(DB_META_JSON,db_meta_new)
                    db_meta = db_meta_new
            case 'drop_table':
                if len(args) < 2:
                    print('Отсутствует имя таблицы. Введите: [drop_table <имя_таблицы>]')
                    continue
                db_meta_new = core.drop_table(db_meta, args[1])
                if db_meta_new:
                    utils.save_metadata(DB_META_JSON,db_meta_new)
                    db_meta = db_meta_new
            case 'list_tables':
                core.list_tables(db_meta)
            case _:
                print(f'Неизвестная команда "{args[0]}". help - справочная информация.')

def print_help():
    """Prints the help message for the current mode."""
   
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")
