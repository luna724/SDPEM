from tkinter import Tk, filedialog
import inspect
import gradio as gr
from typing import Callable

import shared
from modules.util import Util


def browse_file():
    root = Tk()
    root.attributes("-topmost", True)
    root.withdraw()

    filenames = filedialog.askopenfile()
    if filenames is not None:
        root.destroy()
        return str(filenames.name)
    else:
        filename = "Please select file."
        root.destroy()
        return str(filename)


def browse_directory():
    root = Tk()
    root.attributes("-topmost", True)
    root.withdraw()

    filenames = filedialog.askdirectory()
    if filenames is not None:
        root.destroy()
        return str(filenames)
    else:
        filename = "Please select file."
        root.destroy()
        return str(filename)


def bool2visible(x: bool):
    return gr.update(visible=x)


class ItemRegister:
    def __init__(self, setter: Callable = None):
        """
        :param setter
        setter使用法:
        ```py
        def setter(dicts, k, i):
            dicts[k] = i
            return dicts
        ```
        つまりsetterは辞書、キー、値を受け取り、その辞書に適用する関数を返す
        Noneが渡された場合は例の関数が使用される
        """

        def default_setter(d, k, i):
            d[k] = i
            return d

        self.setter = setter or default_setter

    @staticmethod
    def dynamic_setter(d, k, i, *path):
        """
        辞書にキーと値を登録し、パスが存在しない場合は自動的に作成する
        :param d: ルート辞書
        :param k: 登録するキー
        :param i: 登録する値
        :param path: 辞書内のパス（親キーのリスト）
        """
        # 現在の辞書を探索
        current = d
        for key in path:
            if key not in current:
                current[key] = {}  # キーがない場合は空辞書を初期化
            current = current[key]

        # 最終的に値を設定
        current[k] = i
        return d

    def register(self, *names):
        """
        明示的に複数の変数名を指定して登録するデコレータ
        :param names: 各オブジェクトに対するユニークな名前のリスト
        """

        def decorator(func):
            def wrapper(*args, **kwargs):
                # 関数を実行して戻り値を取得
                result = func(*args, **kwargs)

                # 名前の数と結果の長さをチェック
                if isinstance(result, tuple):
                    if len(names) != len(result):
                        raise ValueError(
                            f"Number of names ({len(names)}) does not match number of return values ({len(result)})."
                        )
                    # 名前を対応付けて登録
                    for name, item in zip(names, result):
                        self.setter(shared.ui_obj, name, item)
                        print(f"Auto-registered: {name} -> {item}")
                else:
                    if len(names) != 1:
                        raise ValueError(
                            f"Single return value but multiple names provided: {names}"
                        )
                    self.setter(shared.ui_obj, names[0], result)
                    print(f"Auto-registered: {names[0]} -> {result}")

                return result  # 元の戻り値を返す

            return wrapper

        return decorator


def checkbox_default(v):
    if Util.isbool(v):
        return bool(v)
    else:
        return None


def isInOrNull(base, target, default=None):
    if target in base:
        return target
    else:
        return default
