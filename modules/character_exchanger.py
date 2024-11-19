import re
from typing import *

from modules.character_template import CharacterTemplate
from modules.lora_installer import LoRADatabaseProcessor
from modules.util import Util


class CharacterExchanger(Util):
    def __init__(self):
        self.processor = LoRADatabaseProcessor()
        self.template_util = CharacterTemplate()

    """v4 Method (common.py:obtain_lora_list:manual())"""
    def get_lora_items(self, key:str) -> tuple:
        rtl = self.template_util.load().keys()
        if not key in rtl:
            raise ValueError(f"Failed. {key} isn't in lora_list")
        lora = self.template_util.load()[key]
        data = lora[1]
        ver = lora[0]

        lora = ""
        name_data = ""
        prompt = ""
        extend = ""
        lora_variables_1 = [False, "", ""]
        lora_variables_2 = [False, "", ""]
        loraislora = True

        verList = {"v4": 0, "v5": 1, "v6": 2}
        ver = verList[ver]

        if ver >= 0:  # v4 and above
            lora = data["lora"]
            name_data = data["name"]
            prompt = data["prompt"]
            extend = data["extend"]

            # return name, data["lora"], data["name"], data["prompt"], data["extend"]
        if ver >= 1:  # v5 and above
            lv = data["lora_variables"]
            lora_variables_1 = [lv[0][0], lv[1][0][0], lv[1][0][1]]
            lora_variables_2 = [lv[0][1], lv[1][1][0], lv[1][1][1]]
            loraislora = data["loraisLoRA"]

        ret = (
            key, lora, name_data, prompt, extend, lora_variables_1, lora_variables_2, loraislora
        )
        return ret

    """v4 Method (ce_all.py)"""
    def extract_lora(self) -> list:
        def get_resizable_lora_list(i: CharacterExchanger):
            lora_raw = i.template_util.load()
            return [
                (lora_raw[x][1]["lora"], x, lora_raw[x][1]["name"])
                for x in list(lora_raw.keys())
            ]

        return [
            (x[0].split(":")[0] + ":" + x[0].split(":")[1] + ":", x[1], x[2])
            for x in get_resizable_lora_list(self)
        ] # なんか複雑なタプルが入ってるリストを返す

    """PEM-v4 Character Exchanger method"""
    def exchange_v4(
            self,
            modes: List[str], # Literal lora, name, prompt
            prv_prompt: str, target_lora: str|None, for_template: bool = False
    ):
        lora_list = self.extract_lora()
        prompt_lora = self.re4prompt_v4(r"(<lora:.*:).*>", prv_prompt)

        target = None
        name = None
        key = None
        # LoRAリストにマッチするものを検出
        for p_lora in prompt_lora:
            for tpl in lora_list:
                if tpl[0] in p_lora:
                    target = tpl[0]
                    key = tpl[1]

                    try:
                        prompt_name = self.re4prompt_v4(tpl[2], prv_prompt)
                        name = prompt_name[0]
                        target = tpl[0]
                        break
                    except IndexError:
                        continue

        if for_template:
            modes = ["prompt", "lora", "name"]

        if name is None or target is None:
            raise ValueError("LoRA Template cannot found.")

        lora_name = re.findall(r"<lora:(.*):", target)[0]

        ## TODO: LoRA Block Weight への対応
        lora_weight = self.re4prompt_v4(rf"<lora:{lora_name}:(.*)>", prv_prompt)[0]

        # 各要素の取得
        prompt = re.sub(rf"<lora:{lora_name}:{lora_weight}>", "$LORA", prv_prompt, count=1)
        key, _, name, ch_prompt, extend, lv1, lv2, loraislora = self.get_lora_items(key)
        if not for_template:
            target_key, target_lora, target_name, target_prompt, target_extend, lv1, lv2, loraislora = self.get_lora_items(target_lora)
        else:
            target_key, target_lora, target_name, target_prompt, target_extend, lv1, lv2, loraislora = self.get_lora_items(key)

        # 処理対象でないものはリセット
        if not "lora" in modes:
            target_key = key

        if "name" in modes:
            prompt = re.sub(
                rf"{name},", "$NAME,", prompt, count=1
            )

        # re4prompt を使用し、prompt から ch_prompt を摘出
        # ひとつづつ対象のキャラの prompt に変換
        if for_template:
            mode = ["prompt"]
            target_prompt = "$PROMPT"

        if "prompt" in modes:
            # プロンプトの再構築
            prompts = [
                p.strip()
                for p in prompt.split(",")
            ]

            # キャラプロンプトの再構築
            target_prompts = [
                p.strip()
                for p in target_prompt.split(",")
            ]
            ch_prompts = [
                p.strip()
                for p in ch_prompt.split(",")
            ]

            cp_indexes = []
            for (i, p) in enumerate(prompts):
                p = p.strip("()[] ")
                # LoRAであるならスキップ
                if re.findall(r":(\d+\.\d+)", p) and p.count(">") > 0: continue
                if p in ch_prompts:
                    cp_indexes.append(i)

            for (index, i) in enumerate(cp_indexes):
                # target_prompts にあるだけ cp_indexes を変換する
                # cp_indexes のほうが少ない場合、元プロンプトを消す
                # target_prompts のほうが少ない場合、後者のifブロックで最後の場所にすべて突っ込む
                try:
                    prompts[i] = target_prompts[index]
                except (IndexError, TypeError):
                    prompts[i] = "#PASS"

                # 最後の値だけ保存
                last = (index, i)

            if not len(target_prompts) == last[0]:
                # prompts を分割、最後の ch_prompts の位置にすべて残りを突っ込む
                prompts = prompts[:last[1] + 1] + target_prompts[last[0] + 1:] + prompts[last[1] + 1:]

            # #PASS を削除後、再生成する
            filtered_prompts = [p for p in prompts if p != "#PASS"]
            prompt = ", ".join(filtered_prompts)

        # 重複カンマを消す (多分いらん)
        while prompt.count(", , ") >= 1:
            prompt = prompt.replace(", , ", ", ")
        if for_template:
            return prompt, f"converted: -> Template mode"

        ## TODO: finalize というか、$LORA などの変換スクリプト
        #prompt = self.generation_finalizer.finalize(prompt, (target_key, (lora_weight, 1.0)))
        return prompt, f"Detected: {key} -> {target_key}"