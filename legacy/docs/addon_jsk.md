## addons/jsks
SD-PEMが起動するJishakuに対するコマンドを追加します。
現在PEM内部にアクセスする特別メゾットはありませんが、インポートを通じてアクセスは可能です。

### PEMが認識する型
#### ファイル形式
- `/addons/jsks/*.py`
    - pyファイル内にある `modules.discord.jsk:JishakuAddon`のサブクラスの `__call__`を discord.ext.commands.Bot() の引数とともに呼び出します
    
    - @bot.event on_message() は on_message を async 関数として定義することで呼び出されます

#### ディレクトリ形式 `ディレクトリ形式は現在サポートされていません`
- `/addons/jsks/*(dir)/addon.py`
    - addon.py にある `modules.discord.jsk:JishakuAddon`のサブクラスの `__call__`を discord.ext.commands.Bot() の引数とともに呼び出します
    - パスへの追加は手動で行います。行わない場合インポートは `import addons.jsks.example.extension_file` のようにルートディレクトリから行います
    - on_message() の処理も同様です    

[サンプルコード](/addons/jsks/example.py)