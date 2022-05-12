DEBUG = 0
INFO = 1
WARNINGS = 2
ERRORS = 3
log_dict = {
    "DEBUG": DEBUG,
    "INFO": INFO,
    "WARNING": WARNINGS,
    "WARNINGS": WARNINGS,
    "WARN": WARNINGS,
    "ERROR": ERRORS,
    "ERRORS": ERRORS
}

class Logger:
    def __init__(self, level):
        self.log_level = level
    def debug(self, *args):
        if self.log_level <= DEBUG:
            print(*args)
    def info(self, *args):
        if self.log_level <= INFO:
            print(*args)
    def warning(self, *args):
        if self.log_level <= WARNINGS:
            print(*args)
    def error(self, *args):
        if self.log_level <= ERRORS:
            print(*args)

Log = Logger(DEBUG)