import os

from jsonutil import JsonUtilities


class PromptAlias:
    def __init__(self):
        self.map_file = JsonUtilities(
            os.path.join(os.getcwd(), "configs/prompt_alias.json")
        )
        self.map = {}
        self.load()

    def load(self) -> dict:
        self.map = self.map_file.read()
        return self.map

    def save(self, new: dict =None) -> dict:
        new_map = new or self.map
        self.map_file.save(new_map)
        return self.load()


    # 追加する
    def add(self, alias: str, prompt: str = "", desc: str = "", tags: list[str] = []) -> str:
        self.save()
        alias = alias.lower().strip()

        if alias in self.map.keys():
            if prompt != "" or prompt is not None:
                return "Alias already exists."
            else:
                return self.remove(alias)
        else:
            self.map[alias] = [1, {"prompt": prompt, "desc": desc, "tags": tags}]
            self.save()
            return "Alias added."


    # 消す
    def remove(self, alias: str) -> str:
        self.save()
        alias = alias.lower().strip()

        if alias in self.map.keys():
            previous_prompt = self.map[alias][1]["prompt"]
            self.map.pop(alias)
            self.save()
            print(f"[PromptAlias]: Removing {alias}.. previous prompt: {previous_prompt}")
            return "Alias removed. Previous prompt: " + previous_prompt
        else:
            return "Alias not found."


    # 取得
    def get(self) -> dict:
        return self.map


    # 変換
    def process_command(self, prompts: str) -> str:
        prompt = prompts.split(",")
        for i, p in enumerate(prompt):
            p = p.strip().lower()
            if p in self.map.keys():
                prompt[i] = self.map[p]["prompt"]

        return ", ".join([p.strip() for p in prompt])