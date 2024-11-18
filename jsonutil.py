import json
import os
from json import JSONDecodeError

"""JsonUtilities用の構築コンフィグ"""
class BuilderConfig:
    def __init__(self):
        # 帰り値が必要かどうか
        self.required:bool = True

class JsonUtilities:
    def __init__(self, path, builderConfig: BuilderConfig=BuilderConfig()):
        self.loadable = False
        real = os.path.abspath(path)
        if not os.path.exists(real):
            if builderConfig.required:
                raise FileNotFoundError(f"at {path}")
            return
        if os.path.splitext(real)[1].lower() != ".json":
            if builderConfig.required:
                raise FileNotFoundError(f"at {path}")
            return
        self.builderConfig = builderConfig
        self.path = real
        self.loadable = True
        return

    def refresh(self, path, builderConfig: BuilderConfig | None = None):
        if builderConfig is None and self.loadable:
            builderConfig = self.builderConfig
        else:
            raise RuntimeError("初期化に失敗した場合、リフレッシュにはbuilderConfigが必要です")
        self.loadable = False
        real = os.path.abspath(path)
        if not os.path.exists(real):
            if builderConfig.required:
                raise FileNotFoundError(f"at {path}")
            return
        if os.path.splitext(real)[1].lower() != ".json":
            if builderConfig.required:
                raise FileNotFoundError(f"at {path}")
            return
        self.builderConfig = builderConfig
        self.path = real
        self.loadable = True
        return

    def read(self):
        if not self.loadable:
            raise ValueError("File Cannot readable bur called read()")

        self.refresh(self.path)
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                json_obj = json.load(f)
        except JSONDecodeError as e:
            if self.builderConfig.required:
                raise e
            print(f"File Reading failed. ({self.path})")
            return None
        return json_obj

    def save(self, data):
        if not self.loadable:
            base = os.path.join(self.path, "..\\")
            if os.path.exists(base) and os.path.isdir(base):
                pass
            elif os.path.exists(os.path.join(base, "..\\")):
                os.makedirs(base, exist_ok=True)
                pass
            else:
                raise ValueError("File cannot readable&directory trees not found")

        self.refresh(self.path)
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2) # type: ignore
        except IOError as e:
            if self.builderConfig.required:
                raise e
            print(f"File Writing failed. ({self.path})")