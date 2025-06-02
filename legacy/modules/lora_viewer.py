import re
from typing import *

from modules.lora_installer import LoRADatabaseProcessor

"""
/configs/lora_database.json を様々な方式で表示する機構を持つクラス
保存、データの取得などには向いていない
"""
class LoRADatabaseViewer:
    def __init__(self):
        self.processor = LoRADatabaseProcessor()

        self.model_id_filter:Set[str] = set()
        self.lora_filter:Set[str] = set()
        self.name_filter:str = ""

    def load(self) -> dict:
        return self.processor.load()

    """
    /database/model_lora用のHTML構築関数
    """
    def generate_html(self):
        def isempty(txt):
            if txt == "":
                return "undefined"
            else:
                return txt
        header = """
                <html>
                <head>
                    <style>
                        table {
                            width: 100%;
                            border-collapse: collapse;
                        }
                        th, td {
                            border: 1px solid #ddd;
                            padding: 8px;
                        }
                        th {
                            background-color: #f2f2f2;
                        }
                        tr:hover {
                            background-color: #f5f5f5;
                        }
                    </style>
                </head> """
        end = """
                    </table>
                </body>
                </html>"""
        table_title = """
                <body>
                    <table>
                        <tr>
                            <th>Name</th>
                            <th>Trigger Words</th>
                            <th>Sellable</th>
                            <th>LoRA Trigger</th>
                            <th>File Name</th>
                            <th>URL</th>
                            <th>API URL</th>
                            <th>Timestamp</th>
                            <th>File SHA256</th>
                        </tr>
                """
        html_content = header + table_title
        data = self.load()

        for key, entries in data.items():
            for entry in entries:
                if (self.model_id_filter != set()):
                    id = re.findall(r"^https://civitai\.com/models/(\d+)/", entry.get("url", ""))
                    if len(id) > 0:
                        id = id[0]
                        if id not in self.model_id_filter:
                            continue

                if (self.lora_filter != set()) and entry.get("lora", "").lower() not in self.lora_filter:
                    continue

                if (self.name_filter != "") and self.name_filter.lower() not in entry.get("name", "undefined").lower():
                    continue

                html_content += f"""
                        <tr>
                            <td>{entry.get('name', 'undefined')}</td>
                            <td>{', '.join(entry.get('trigger_words', []))}</td>
                            <td>{'Yes' if entry.get('sellable', False) else 'No'}</td>
                            <td>{isempty(entry.get('lora', 'undefined'))}</td>
                            <td>{isempty(entry.get('file_name', 'unknown'))}</td>
                            <td><a href="{entry.get('url', '#')}" target="_blank" rel="noopener noreferrer">CivitAI</a></td>
                            <td><a href="{entry.get('api_url', '#')}" target="_blank" rel="noopener noreferrer">Download</a></td>
                            <td>{entry.get('timestamp', '').split(".")[0]}</td>
                            <td>{key}</td>
                        </tr>
                        """

        html_content += end
        return html_content

    """
    Syntax: $modelID={modelID} $lora={LoRA} or {name}
    """
    def add_filter(self, text: str, keyword_enable: bool=False):
        text = text.lower().replace("\n", " ")
        if keyword_enable:
            trig_ids = re.findall(
                r"\$modelid=(\d+);?", text
            )
            trig_lora = re.findall(
                r"\$lora=(\w+);?", text
            )

            # テキストを再処理
            self.model_id_filter = set()
            for id in trig_ids:
                if f"$modelid={id}" in text:
                    self.model_id_filter.add(id)
                    text = re.sub(
                        rf"(\$modelid={id};?)", "", text
                    )
                else:
                    print(f"[ERROR]: Unknown Exception in LoraDatabaseViewer.add_filter() \n(id: {id} / text: {text})")

            self.lora_filter = set()
            for lora in trig_lora:
                if f"$lora={lora}" in text:
                    self.lora_filter.add(lora)
                    text = re.sub(
                        rf"(\$lora={lora};?)", "", text
                    )
                else:
                    print(f"[ERROR]: Unknown Exception in LoraDatabaseViewer.add_filter() \n(lora: {lora} / text: {text})")

        self.name_filter = text.strip()

    """
    データベースに存在するLoRAの名前またはトリガーまたはファイル名を返す
    """
    def all_lora(self, mode:Literal["name", "trigger", "fn"]):
        lists = self.load()
        rtl = []
        for c in lists.values():
            c = c[0]
            if mode.lower() == "name":
                add2 = c.get('name', None)
            elif mode.lower() == "trigger":
                add2 = c.get('lora', None)
            elif mode.lower() == "fn":
                add2 = c.get('file_name', None)
            else:
                break

            if add2 is None: continue
            rtl.append(add2)
        return rtl