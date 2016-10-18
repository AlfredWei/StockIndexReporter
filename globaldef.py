from colorama import *


class ErrorLevel:
    ERROR = 1
    WARNING = 2
    SUCCESS = 3
    HIGHLIGHT = 4
    VERBOSE = 5


verbose_level = ErrorLevel.SUCCESS

StyleColor = {
    ErrorLevel.ERROR: Fore.RED,
    ErrorLevel.WARNING: Fore.YELLOW,
    ErrorLevel.SUCCESS: Fore.GREEN,
    ErrorLevel.HIGHLIGHT: Fore.MAGENTA,
}


def elog(msg_level, *args, **argd):
    if msg_level > verbose_level:
        return
    try:
        if msg_level not in StyleColor:
            print(*args, **argd)
        else:
            # print(Fore.RESET + Back.RESET + Style.RESET_ALL)
            print(StyleColor[msg_level], *args, **argd)
    except:
        print(Fore.RESET)
