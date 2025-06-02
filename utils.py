import datetime

class AnsiColors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'
    RESET = '\033[0m'

def now():
  return datetime.datetime.now().strftime("%H:%M:%S")

def println(*args, **kw):
  return print(f"{AnsiColors.GRAY}[{now()}] {AnsiColors.GREEN}INFO{AnsiColors.RESET} {' '.join(map(str, args))}", **kw)

def printerr(*args, **kw):
  return print(f"{AnsiColors.GRAY}[{now()}] {AnsiColors.RED}ERROR{AnsiColors.RESET} {' '.join(map(str, args))}", **kw)

def printwarn(*args, **kw):
  return print(f"{AnsiColors.GRAY}[{now()}] {AnsiColors.YELLOW}WARN{AnsiColors.RESET} {' '.join(map(str, args))}", **kw)

def print_critical(*args, **kw):
  return print(f"{AnsiColors.GRAY}[{now()}] {AnsiColors.BOLD}{AnsiColors.RED}CRITICAL!{AnsiColors.RESET} {' '.join(map(str, args))}", **kw)