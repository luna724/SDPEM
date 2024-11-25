import json
import os
from json import JSONDecodeError

class BuilderConfig:
    """JsonUtilities用の構築コンフィグ"""
    def __init__(self):
        # 帰り値が必要かどうか
        self.required:bool = True

        # 新規生成を許可するか
        self.allow_make_new:bool = True

class JsonUtilities:
    def __init__(self, path, builderConfig: BuilderConfig=BuilderConfig()):
        self.loadable = False
        real = os.path.abspath(path)
        if not os.path.exists(real):
            if os.path.exists(os.path.join(real, "..\\")) and builderConfig.allow_make_new:
                with open(real, "w", encoding="utf-8") as f:
                    json.dump({}, f) # type: ignore
                print("[JsonUtilities]: Files not exists. making new..")
            else:
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

    def make_dynamic_data(self, data:dict|None = None):
        """json、辞書形式のデータをpydanticのようなクラス形式のデータ形式に変換する
        返還後のデータは動的に生成されるため、型チェックなどには適していない"""
        class DynamicObject:
            def __init__(self, dictionary):
                self.raw = dictionary
                for key, value in dictionary.items():
                    if isinstance(value, dict):
                        # ネストされた辞書があれば再帰的にDynamicObjectに変換
                        value = DynamicObject(value)
                    setattr(self, key, value)

            def __repr__(self):
                return f"<DynamicObject {self.__dict__}>"

            def __call__(self):
                return self.raw
        if data is None:
            data = self.read()
        return DynamicObject(data)