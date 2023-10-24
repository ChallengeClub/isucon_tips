# Remote SSH プラグインのインストール
VSCodeの左上からインストール

# ssh config に ssh 接続情報を追加

/Users/ユーザ名/.ssh/config に以下の内容を追加する。
```bash
Host [ホスト名]
  HostName [接続先]
  Port [ポート]
  IdentityFile [鍵認証のパス]
  User [接続ユーザー名]
```

ssh接続時のコマンドが
```bash
$ ssh -p 30022 kiwasa@35.78.193.49 -i ~/.ssh/id_rsa_kiwsa
```
の場合、以下になる。
```bash
$ sudo nano ~/.ssh/config
Host isucon12q1
     User kiwasa
     HostName 35.78.193.49
     Port 22
     IdentityFile ~/.ssh/id_rsa_kiwsa
```

configを記載すると、
```bash
$ ssh [ホスト名]
```
で接続できるようになる。

# VSCodeでSSH接続

左下の`><`みたいなアイコン→SSH Targetから、上記で接続したホスト名を選択する。新しいVSCodeのウィンドウが表示される。

もしくは、左のRemote Explorerアイコンをクリック→ REMOTES SSHに先ほど登録したホスト名が表示されるので、クリックすると新しいウィンドウが起動する。

# max_user_watches の変更
このままだと大規模のファイルが見れなくなるので、max_user_watchesを変更する
```bash
$ cat /proc/sys/fs/inotify/max_user_watches
8192
$ sudo nano /etc/sysctl.conf
~~~ 追記
# max_user_watches
fs.inotify.max_user_watches=524288
```

```bash
$ sudo sysctl -p
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
fs.inotify.max_user_watches = 524288
```

```bash
$ cat /proc/sys/fs/inotify/max_user_watches
524288
```
監視できるファイルの最大数が524,288とのこと。
各ファイル ウォッチは 1080 バイトを使用するため、524,288 個のウォッチがすべて消費されると仮定すると、上限は約 540 MiB になるので、メモリ制約のある場合は数を減らしておく。

# VSCodeがサーバリソースを食い散らかす

複数人でVSCodeのRemote SSHで接続していたサーバーの反応が異常に遅くなることがあった。

(【VSCode使用者注意】サーバーリソース食い散らかすﾏﾝから解放される唯一の方法)[https://blog.masuyoshi.com/%E3%80%90vscode%E4%BD%BF%E7%94%A8%E8%80%85%E6%B3%A8%E6%84%8F%E3%80%91%E3%82%B5%E3%83%BC%E3%83%90%E3%83%BC%E3%83%AA%E3%82%BD%E3%83%BC%E3%82%B9%E9%A3%9F%E3%81%84%E6%95%A3%E3%82%89%E3%81%8B%E3%81%99/]

記事によると、VSCodeでSSH接続する際にサーバーに負荷をかけてしまうことがあるらしい。

対策として、ファイル監視を無効化する。
1. 画面上部メニュー「ファイル」→「ユーザー設定」→「設定」を選択
2. 「設定の検索」に Watcher Exclude と入力
3. 「パターン追加」 から ** を追加する
4. 設定を反映させるために、VSCodeを再起動


※ デメリットあり
> ただし、トレードオフとして、gitのファイル変更状況がリアルタイムで反映されなくなるので、自身でコミットなどをする際には、手動でファイルの変更を確認することになります。

手動でリロードしなければならない。