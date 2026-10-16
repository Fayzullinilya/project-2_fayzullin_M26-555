import prompt


def command_help():
    print('<command> exit - выйти из  программы')
    print('<command> help - справочная информация')

def welcome():
    print('\nПервая попытка запустить проект!')
    print('\n***')
    command_help()

    while True:
        command = prompt.string('Введите команду: ')
        match command:
            case 'help':
                command_help()
            case 'exit':
                break