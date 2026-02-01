# Database Logger Module

データベースロガーモジュールは、SDPEM の生成ログとタグ統計を管理するためのシステムです。

## 概要

このモジュールは2つの主要な機能を提供します：

### A. 生成ログ (Generation Log)
1回の生成ごとに1レコードを作成し、JSONL形式で保存します。

**保存場所**: `assets/generation_records.jsonl`

**フィールド**:
- `id`: UUID - 生成の一意識別子
- `timestamp`: float - 生成時刻 (Unix timestamp)
- `user_action`: str | null - ユーザー評価 ("keep" または "discard")
- `prompt_tags`: List[str] - 生成時に指定したタグリスト（正規化済み）
- `inferred_tags`: List[InferredTag] - 生成画像からTaggerで検出したタグリスト（信頼度スコア付き）
- `mismatch_data`: MismatchData - 入出力のミスマッチ情報
  - `lost`: List[str] - Inputにはあるが Outputで検出されなかったタグ
  - `ghost`: List[str] - Inputにはないが Outputで強く検出されたタグ (score > 0.7)
- `info_text`: str - 生成時のinfotxt
- `param`: str - SDPEM の生成パラメータ（JSON文字列化）

### B. タグ統計マスタ (Tag Stats Master)
全ログから集計・更新されるタグごとの成績表。個別のJSON ファイルとして管理されます。

**保存場所**: `assets/tag_stats/{tag_name}.json`
- 特殊文字（`< > : " / \ | ? *` など）は `？` に置換されます

**フィールド**:
- `tag_name`: str - タグ名
- `usage_count`: int - 使用回数
- `detection_count`: int - 検出回数
- `keep_count`: int - Keepされた回数
- `detection_rate`: float - (検出回数 / 使用回数) × 100 (%)
- `keep_rate`: float - (Keepされた回数 / 使用回数) × 100 (%)
- `cooccurrence`: List[TagCooccurrence] - 共起するタグのリスト（Top 20）
  - `tag`: str - タグ名
  - `frequency`: int - 共起頻度
- `conflicts`: List[TagConflict] - 同時使用時にDetection Rateが下がるタグのリスト
  - `tag`: str - タグ名
  - `impact`: float - 影響度 (0.0 ～ 1.0)

## 使用方法

### 基本的な使い方

```python
from modules.database.logger import GenerationLogger, TagStatsManager

# 初期化（デフォルトパスを使用）
logger = GenerationLogger()
manager = TagStatsManager()

# 生成ログを保存
log = logger.save_log(
    prompt_tags=["1girl", "blonde_hair", "blue_eyes"],
    inferred_tags=[
        {"tag": "1girl", "score": 0.95},
        {"tag": "blonde_hair", "score": 0.88},
        {"tag": "blue_eyes", "score": 0.82},
    ],
    info_text="Steps: 20, Sampler: DPM++ 2M Karras, ...",
    param={
        "prompt": "1girl, blonde hair, blue eyes",
        "steps": 20,
        "cfg_scale": 7.0
    },
    user_action="keep"
)

# タグ統計を更新
manager.update_from_log(log)
```

### ログの読み込み

```python
# すべてのログを読み込む
all_logs = logger.read_logs()

# 最新の10件のみ読み込む
recent_logs = logger.read_logs(limit=10)

# ログを処理
for log in recent_logs:
    print(f"ID: {log.id}")
    print(f"Tags: {', '.join(log.prompt_tags)}")
    print(f"Lost: {log.mismatch_data.lost}")
    print(f"Ghost: {log.mismatch_data.ghost}")
```

### タグ統計の取得

```python
# 特定のタグの統計を読み込む
stats = manager.load_tag_stats("1girl")

if stats:
    print(f"使用回数: {stats.usage_count}")
    print(f"検出率: {stats.detection_rate:.1f}%")
    print(f"Keep率: {stats.keep_rate:.1f}%")
    print(f"共起タグ:")
    for cooccur in stats.cooccurrence[:5]:
        print(f"  - {cooccur.tag}: {cooccur.frequency}回")
```

### バッチ処理

```python
# 既存のすべてのログから統計を再計算
logs = logger.read_logs()
manager.batch_update_from_logs(logs)
```

### カスタムパスの使用

```python
# デフォルト以外のパスを使用する場合
logger = GenerationLogger(records_path="custom/path/records.jsonl")
manager = TagStatsManager(stats_dir="custom/path/stats")
```

## 統合例

Tagger と統合した実際の使用例：

```python
from modules.database.logger import GenerationLogger, TagStatsManager
from modules.tagger.predictor import OnnxRuntimeTagger
from PIL import Image

# 初期化
logger = GenerationLogger()
manager = TagStatsManager()
tagger = OnnxRuntimeTagger("model_name")

# 画像を生成後...
generated_image = Image.open("generated.png")

# プロンプトからタグを抽出（正規化済み）
prompt_tags = ["1girl", "blonde_hair", "blue_eyes"]

# Taggerで画像を解析
general_res, character_res, rating = await tagger.predict(
    generated_image, 
    threshold=0.5, 
    character_threshold=0.7
)

# Tagger の結果を変換
inferred_tags = [
    {"tag": tag, "score": score} 
    for tag, score in general_res.items()
]

# ログを保存
log = logger.save_log(
    prompt_tags=prompt_tags,
    inferred_tags=inferred_tags,
    info_text=generation_info_text,
    param=generation_parameters,
    user_action=None  # 後でユーザーが評価
)

# 統計を更新
manager.update_from_log(log)
```

## Pydantic モデル

このモジュールは Pydantic を使用してデータ検証と型安全性を提供します：

- `GenerationLog` - 生成ログのメインモデル
- `InferredTag` - 推論されたタグと信頼度スコア
- `MismatchData` - ミスマッチ情報
- `TagStats` - タグ統計のメインモデル
- `TagCooccurrence` - 共起タグ情報
- `TagConflict` - 競合タグ情報

すべてのモデルは `model_dump_json()` と `model_validate_json()` をサポートしています。

## ファイル構造

```
SDPEM/
├── modules/
│   └── database/
│       ├── __init__.py
│       ├── logger.py          # メインロジック
│       ├── example_usage.py   # 使用例
│       └── README.md          # このファイル
└── assets/
    ├── generation_records.jsonl  # 生成ログ (JSONL形式)
    └── tag_stats/                # タグ統計ディレクトリ
        ├── 1girl.json
        ├── blonde_hair.json
        └── ...
```

## 注意事項

1. **ファイルパス**: デフォルトのパスはプロジェクトルートからの相対パスです。絶対パスも使用可能です。

2. **特殊文字**: タグ名に含まれるファイルシステムで無効な文字（`< > : " / \ | ? *`）は `？` に自動的に置換されます。

3. **並行処理**: 複数のプロセスから同時に書き込む場合は、適切な排他制御が必要です。

4. **データの永続性**: `assets/` ディレクトリは `.gitignore` に含まれており、ユーザーデータとして扱われます。

## ライセンス

このモジュールは SDPEM プロジェクトの一部であり、同じライセンスの下で配布されます。
