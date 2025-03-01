import os.path

from jsonutil import JsonUtilities


class Webhook:
    def __init__(self):
        self.file = JsonUtilities(
            os.path.join(os.getcwd(), "webhook.json")
        )
        self.load_config()


    def load(self) -> dict:
        return self.file.read()

    def save(self, data: dict):
