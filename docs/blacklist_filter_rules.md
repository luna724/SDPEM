# Blacklist Filter Rules

このドキュメントは、ブラックリストフィルタルール機能について説明します。

## 概要

ブラックリストフィルタルールは、通常ブラックリストでフィルタされるタグを、特定の条件下でフィルタせずに残す機能です。

## 使用例

### 例1: 特定のタグが含まれていない場合に残す (not_has)

**シナリオ:** `blindfold` がブラックリストに登録されているが、`looking at viewer` が含まれていない場合は `blindfold` を残したい

**入力1:** `blindfold, looking at viewer, open eyes`
**出力1:** `looking at viewer, open eyes` (looking at viewerが含まれているためblindfoldはフィルタされる)

**入力2:** `blindfold, open eyes, open mouth`
**出力2:** `blindfold, open eyes, open mouth` (looking at viewerが含まれていないためblindfoldは残る)

### 例2: 特定のタグが含まれている場合に残す (has)

**シナリオ:** `red eyes` がブラックリストに登録されているが、`vampire` が含まれている場合は `red eyes` を残したい

**入力1:** `red eyes, vampire, pale skin`
**出力1:** `red eyes, vampire, pale skin` (vampireが含まれているためred eyesは残る)

**入力2:** `red eyes, angry, clenched teeth`
**出力2:** `angry, clenched teeth` (vampireが含まれていないためred eyesはフィルタされる)

## 設定ファイル

### 設定ファイルの場所

- デフォルト設定: `defaults/DEF/!blacklist_filter_rules.json`
- ユーザー設定: `config/blacklist_filter_rules.json`

### ルールの構造

```json
{
  "rule_name": {
    "name": "rule_name",
    "description": "ルールの説明",
    "enabled": true,
    "version": 1.0,
    "data": {
      "version": 1.0,
      "target": "フィルタ対象のタグ",
      "rule_type": "not_has",
      "conditions": ["条件タグ1", "条件タグ2"],
      "is_pattern": false,
      "flags": ["IGNORECASE"]
    }
  }
}
```

### パラメータ説明

#### トップレベル
- `name` (string): ルールの名前
- `description` (string): ルールの説明
- `enabled` (boolean): ルールを有効にするかどうか
- `version` (number): ルールのバージョン

#### data オブジェクト
- `target` (string): このルールが適用されるブラックリストタグ
- `rule_type` (string): ルールのタイプ
  - `"not_has"`: 条件タグが**含まれていない**場合にターゲットを残す
  - `"has"`: 条件タグが**含まれている**場合にターゲットを残す
- `conditions` (array): 条件となるタグのリスト
- `is_pattern` (boolean): targetとconditionsを正規表現として扱うか
- `flags` (array): 正規表現のフラグ (例: `["IGNORECASE"]`)

## ルールタイプの詳細

### not_has (条件が含まれていない場合に残す)

複数の条件がある場合、**すべての条件が含まれていない**場合にのみターゲットを残します。

例: `conditions: ["sword", "knight"]`
- `"weapon, gun, modern"` → weaponを残す (swordもknightも含まれていない)
- `"weapon, sword, battle"` → weaponをフィルタ (swordが含まれている)
- `"weapon, knight, armor"` → weaponをフィルタ (knightが含まれている)

### has (条件が含まれている場合に残す)

複数の条件がある場合、**すべての条件が含まれている**場合にのみターゲットを残します。

例: `conditions: ["vampire", "gothic"]`
- `"red eyes, vampire, gothic, pale"` → red eyesを残す (両方含まれている)
- `"red eyes, vampire, modern"` → red eyesをフィルタ (gothicが含まれていない)
- `"red eyes, gothic, night"` → red eyesをフィルタ (vampireが含まれていない)

## パターンマッチング

`is_pattern: true` を設定すると、targetとconditionsを正規表現として使用できます。

### 例: パターンを使用したルール

```json
{
  "pattern_example": {
    "name": "pattern_example",
    "description": "パターンマッチングの例",
    "enabled": true,
    "version": 1.0,
    "data": {
      "version": 1.0,
      "target": ".*blind.*",
      "rule_type": "not_has",
      "conditions": ["viewer"],
      "is_pattern": true,
      "flags": ["IGNORECASE"]
    }
  }
}
```

このルールは `blindfold`, `blind`, `blinded` など、"blind" を含むすべてのタグにマッチします。

## 実装の詳細

### モジュール構造

- `modules/blacklist.py`: BlacklistFilterRule と BlacklistFilterRuleManager クラス
- `modules/prompt_processor.py`: フィルタルールの統合

### プログラムからの使用

```python
from modules.blacklist import blacklist_filter_rules

# ルールのリロード
await blacklist_filter_rules.reload()

# 新しいルールの追加
rule_data = {...}
blacklist_filter_rules.push("new_rule", rule_data)

# ルールの更新
blacklist_filter_rules.update("existing_rule", updated_data)

# ルールの削除
blacklist_filter_rules.delete("rule_name")
```

## 注意事項

1. ルールは `modules/prompt_processor.py` の `proc_blacklist()` 内で自動的に適用されます
2. LoRAトリガータグは常に保持され、フィルタされません
3. 複数のルールが同じターゲットにマッチする場合、最初にマッチしたルールが適用されます
4. ルールが無効 (`enabled: false`) の場合、そのルールは無視されます

## テスト

テストファイル:
- `test_blacklist_minimal.py`: 基本的なルールロジックのテスト
- `test_blacklist_filter.py`: 完全な統合テスト (依存関係が必要)

テストの実行:
```bash
python test_blacklist_minimal.py
```
