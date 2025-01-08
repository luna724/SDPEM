import os

from modules.character_template import CharacterTemplate

def character(accept_v3: bool = True):
    print("Working dir: ", os.getcwd())
    ct = CharacterTemplate()
    ct.template_updater(update_v3 = not accept_v3)
    print("Success!")



if __name__ == "__main__":
    character(False)