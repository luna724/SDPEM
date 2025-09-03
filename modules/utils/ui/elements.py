import gradio as gr
from typing import Any

from gradio_client.serializing import SimpleSerializable

#@codex
class HiddenValue(gr.components.base.IOComponent):
    """
    UIには表示されず、任意の値を
    gr.Button.click() の inputs に渡すための隠しコンポーネント。

    Gradio の API 情報生成時にシリアライザを要求されないよう、
    コンポーネント種別は "state" として振る舞います（API からは無視される）。
    """

    allow_string_shortcut = False

    def __init__(self, value: Any = None, **kwargs):
        # 完全非表示・非対話にして値をそのまま保持
        super().__init__(value=None, visible=False, interactive=False, **kwargs)
        # IOComponent.__init__ は postprocess(value) を通すため、改めて値を保持
        self.value = value

    # Blocks の設定上、このコンポーネントを "state" として扱わせる
    # （gradio_client.utils.SKIP_COMPONENTS により API 情報から除外される）
    def get_block_name(self) -> str:  # type: ignore[override]
        return "state"

    # payload には依存せず、保持している値をそのまま関数へ渡す
    def preprocess(self, payload):  # type: ignore[override]
        return self.value

    # 出力としては何も返さない（見えないため）
    def postprocess(self, value):  # type: ignore[override]
        return None

    # Serializable の要件を満たすために実装（実際は API 生成からはスキップされる）
    def api_info(self):  # type: ignore[override]
        return SimpleSerializable().api_info()

    def example_inputs(self):  # type: ignore[override]
        return {"raw": None, "serialized": None}
