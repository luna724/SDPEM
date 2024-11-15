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
        real = os.path.realpath(path)
        if os.path.exists(real):
            if builderConfig.required:
                raise FileNotFoundError(f"at {path}")
            return
        if os.path.splitext(real)[1].lower() == ".json":
            return
        elif os.path.splitext(real)[1].lower != ".json":
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
        real = os.path.realpath(path)
        if os.path.exists(real):
            if builderConfig.required:
                raise FileNotFoundError(f"at {path}")
            return
        if os.path.splitext(real)[1].lower() == ".json":
            return
        elif os.path.splitext(real)[1].lower != ".json":
            if builderConfig.required:
                raise FileNotFoundError(f"at {path}")
            return
        self.builderConfig = builderConfig
        self.path = real
        self.loadable = True
        return

    def read(self):
        if not self.loadable:
            raise ValueError("File Cannot readable while called read()")

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