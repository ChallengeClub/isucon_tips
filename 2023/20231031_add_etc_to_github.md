# 本日のサマリー
- おかしくなったサーバーをリセットしたので、細々とした設定を戻そうとした
- パッケージのインストールや設定変更は、シェルスクリプト化しようとした
- サーバーを設定するには、/etc/の編集が必要になった
- /etc/の編集を履歴管理できるように、webappのgitリポジトリに入れようとした
- 本番に備えて、githubのリポジトリとアカウントの運用を考え始めたら、学びが深かった
- 最終的に
  - webappと/etc/を、[kiwsさんのISUCON専用アカウント](https://github.com/kiws-isucon-bot)の[リポジトリ](https://github.com/kiws-isucon-bot/isucon12q3-testbot)にpushできた
  - シェルスクリプト2本を、[isucon_tools](https://github.com/ChallengeClub/isucon_tools)にpushできた
 
# Elastic IPアイスブレイク再び
「先週のElastic IPがなんちゃらって何ですか?」 -> 「EC2インスタンスに固定IPを関連付けたので、もうIPアドレス変わらないんですよ〜」<br>
「それってどうやって確認するんですか?」 -> AWSにログインして、isucon12q3のElastic IPを見ると分かります〜」

確認したIPアドレスでログイン完了。

# パッケージのインストール
## ツール
本番含め、慣れたツールが一番。
- ともさん: `sudo apt install emacs-nox`
- kiwsさん: gitkを入れたいが、パッケージ名が不明
```
$ gitk
Command 'gitk' not found, but can be installed with:
sudo apt install gitk
```
ということで、`sudo apt install gitk`でインストール。ところが、実行すると
```
$ gitk
application-specific initialization failed: no display name and no $DISPLAY environment variable
Error in startup script: no display name and no $DISPLAY environment variable
    while executing
"load /usr/lib/x86_64-linux-gnu/libtk8.6.so"
    ("package ifneeded Tk 8.6.12" script)
    invoked from within
"package require Tk"
    (file "/usr/bin/gitk" line 10)
```
ということで、sshでログインしたCLIからは、(そのままでは)GUIは表示できない模様。TODO。

## Prometheus
[以前のtips](https://github.com/ChallengeClub/isucon_tips/blob/main/2023/20230921_node-exporter.md)より、
```
sudo apt -y install prometheus prometheus-node-exporter
```
を`~isucon/bin/10_install_packages.sh`に記入、実行。Prometheusがインストールされた。<br>
http://admin.t.isucon.local:9090/ にアクセスし、[呪文](https://github.com/ChallengeClub/isucon_tips/blob/main/2023/20230921_node-exporter.md#prometheus%E7%A2%BA%E8%AA%8D)を入力、Executeボタンを押し、グラフ表示も確認OK。

# TODO
- gitk over ssh
- `~isucon/isucon_tools/10-install-packages.sh`を`10_install_packages.sh`に`git mv`して`git push origin main`したら、ユーザー名とパスワードを聞かれてしまった…`~/.cache/git/credential/`が空だからか? 謎。
