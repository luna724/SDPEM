import psutil
import os

def get_current_ram_mb() -> float:
    process = psutil.Process(os.getpid()).memory_info().rss
    return process / (1024 * 1024)