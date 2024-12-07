import psutil
import GPUtil
from cpuinfo import get_cpu_info as _get_cpu_info
from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo, nvmlDeviceGetTemperature, nvmlDeviceGetName, nvmlShutdown

def get_gpu_info():
    nvmlInit()
    gpus = []
    try:
        gpu_count = len(GPUtil.getGPUs())
        for i in range(gpu_count):
            handle = nvmlDeviceGetHandleByIndex(i)
            memory = nvmlDeviceGetMemoryInfo(handle)
            temperature = nvmlDeviceGetTemperature(handle, 0)  # 0 = GPU 温度
            name = nvmlDeviceGetName(handle).encode('utf-8')
            gpus.append({
                'id': i,
                'name': name,
                'vram_used': memory.used // (1024 ** 2),  # MBに変換
                'vram_total': memory.total // (1024 ** 2),  # MBに変換
                'temperature': temperature
            })
    finally:
        nvmlShutdown()
    return gpus

def get_cpu_info():
    cpu_info = _get_cpu_info()
    cpu_temp = None
    try:
        # CPU温度取得 (Linuxや特定のシステムでのみ動作)
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if "coretemp" in temps:
                cpu_temp = temps["coretemp"][0].current
    except Exception:
        pass

    return {
        'name': cpu_info['brand_raw'],
        'usage': psutil.cpu_percent(interval=1),
        'clock_speed': psutil.cpu_freq().current if psutil.cpu_freq() else None,
        'temperature': cpu_temp
    }

def get_ram_info():
    virtual_memory = psutil.virtual_memory()
    return {
        'used': virtual_memory.used // (1024 ** 2),  # MBに変換
        'total': virtual_memory.total // (1024 ** 2)  # MBに変換
    }