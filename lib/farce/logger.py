import traceback
from colorama import Fore


class Logger:
    def catchment(self, callback):
        def catcher(*args, **kwargs):
            try:
                return callback(*args, **kwargs)
            except Exception as err:
                self.error(err)

        return catcher

    def error(self, err: Exception | str):
        if isinstance(err, Exception):
            err = ''.join(traceback.format_exception(err))
        print(Fore.RED + "ERROR" + Fore.RESET + ":", err)

    def log(self, smth: any):
        print(Fore.YELLOW + "LOG" + Fore.RESET+":", smth)
