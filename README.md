# SD-PEM
#### Stable-Diffusion Prompt-EasyMaker 
[![wakatime](https://wakatime.com/badge/user/a3dc88bc-f773-46f5-86f8-abb56f21a04b/project/469bda6f-d8fe-424e-a9c1-925cf7aea869.svg)](https://wakatime.com/badge/user/a3dc88bc-f773-46f5-86f8-abb56f21a04b/project/469bda6f-d8fe-424e-a9c1-925cf7aea869)

- Q. これはなんやねん <br>
A. 限定的な状況において、画像生成を便利にするスクリプトです

- Q. どんな状況やねん <br>
A. プロンプト作りたくないときとか、同じプロンプトをキャラごとに試したいときとか

| Current   | v1.0-preview |
|-----------|--------------|
| Recommend | v1.0-preview |

## 依存関係 /　Dependencies
- [VisualStudio-BuildTools](https://aka.ms/vs/17/release/vs_BuildTools.exe)
- [Python 3.10+](https://www.python.org/downloads/)
- `AUTOMATIC1111/stable-diffusion-webui` or `lllyasviel/stable-diffusion-webui-forge`

## 入れ方 
1. 依存関係をダウンロード
2. リポジトリをクローン (`git clone https://github.com/luna724/SDPEM SDPEM`)
3. `a1111_webui_pth.json`にて`Stable-Diffusion-WebUI`の位置を設定
4. `Stable-Diffusion-Webui`を`webui-api.bat`にて実行する
5. PEM側の`v5β-full.bat`を実行

## ヘルプ / help
- [使用可能な引数](/docs/arguments.md)
- [サポート状況](/Support.md)

## 各機能使用方法 / features
- [`Generation/from LoRA`](/docs/generation/from_lora.md)
- [`Model-Installer/LoRA`](/docs/model_installer/lora.md)
- [`Database-Viewer/LoRA (Models)`](/docs/database_viewer/lora_models.md)
