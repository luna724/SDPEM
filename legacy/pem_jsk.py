import modules.discord.jsk as jsk
from initialize import search_sd_webui_at1

def run():
    search_sd_webui_at1()
    jsk.start_jsk()

if __name__ == "__main__":
    print("[Jishaku]: Starting jishaku bot in subprocess")
    run()