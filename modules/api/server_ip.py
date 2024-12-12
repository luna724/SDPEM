import requests

from jsonutil import JsonUtilities
import os
import gradio as gr

class _ServerIP:
    def __init__(self):
        self.file = JsonUtilities(
            os.path.join(os.getcwd(), "configs/server_ip.json")
        )

        self.ip = self.file.read()["ip"]
        self.port = self.file.read()["port"]

    def _file(self):
        data = self.file.read()
        data["ip"] = self.ip
        data["port"] = self.port
        self.file.save(data)

    def _validate(self):
        url = f"http://{self.ip}:{self.port}"
        try:
            req = requests.get(url)
            if req.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def new(self, ip, port):
        self.ip = ip
        self.port = port
        if self._validate():
            gr.Info("Successfully updated!", duration=5)
            self._file()
        else:
            raise gr.Error("Unable to connect to server. re-check the values and try again.")

server_ip = _ServerIP()