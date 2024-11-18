# UI config の値とその内容、内部システムを記録

| 値 | キー | デフォルト | 内容 | システム的動作 |
| --- | --- | --- | --- | --- |
| LoRA Variableの表示 | enable_lora_variable_showcase | True | Generate にて LoRA Variableの表示トグル | 内部的には、表記が常に False になるだけで処理は行われている |
| Compact Example Viewer の自動実行 | auto_run_compact_example_viewer | True | Generate にて Template を選択した際に Compact Example Viewer を自動実行する。この機能の手動実行には `show_optin_values` の compact_example_viewer を有効化する必要がある | 内部的には、Falseの場合処理を行わない |
| LoRA Optsの自動設定 | auto_setup_lora_opts | True | Generateにて LoRA Weight / Extend Prompt をテンプレートの値に沿って自動設定する | 内部的には、Falseの場合処理を行わない |
