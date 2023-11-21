# ISUCON13 本戦RUNBOOK

## 【前日準備】
- [x] Team登録/githubにssh公開鍵登録/AWS起動試験  
- [x] 当日用のDiscordPrivateChannel/VoiceChannel用意
- [ ] 当日用の空のPrivareリポジトリ用意
- [ ] 各自github PAT発行とPrivareリポジトリ接続確認  
- [ ] Team代表はAWSクーポン入手  
- [ ] お昼ごはん、おやつ、ドリンク、睡眠  

## 【当日競技開始】
> **Info:**   10:00 競技開始。競技当日の流れは11/21目途に発表予定。
  
11/21発表の競技当日の流れを事前読んでおいて、当日は当日発表されるisucon13本戦当日マニュアルを読む。  
内容に応じてRUNBOOKは読み替える。isucon13 Discordは都度確認する。  

### ■起動
[ここ](./20231003_cloudFormation.md)を参考に以下の作業を行う。
- [ ] [ISUCON13 Portal](https://portal.isucon.net/auth/settings/team/)からCloudFormationのテンプレートをダウンロード。  
- [ ] ダウンロードしたテンプレートファイルを元にAWSでスタックを作成しCREATE_COMPLETEを待つ。  

### ■接続
同一インスタンスx3が作成される前提で各自の作業用に１インスタンスを使う想定にしましょう。  
（.ssh/configへ全インスタンス(isucon13fxとか)のIPアドレス追記するのがお薦め。）  
- [ ] 出来たインスタンスに各自ssh接続する。成功したらsudo su - isuconまで実施。  
- [ ] ~/webapp/binを作成しisucon_toolsをgit cloneする。  
- [ ] 04_setupSSH.shを実行してssh keepalive設定を行う。  
- [ ] 必要なメンバーはVSCodeRemoteDevelopの接続等を設定（autoscanはoffで）  

### ■サーバ内部調査
下記などでインスタンスの概要調査を行う。  
```
$ cat /etc/os-release                   # os確認  
$ cat /etc/passwd | grep -v nologin     # user確認  
$ sudo lsof -P -i | grep -v sshd        # process確認
$ sudo ss -tlp | grep hoge              # process確認
$ sudo ss -tlpn | grep hoge             # process確認
$ service --status-all                  # serviceリスト確認
$ systemctl list-unit-files -t service | grep enabled  # serviceリスト確認
$ systemctl status hoge                 # service確認
$ file hoge                             # file素性確認
$ cat /etc/hosts                        # サイト情報が何か有るかも
```
想定ではWebサーバ(nginx)やRDB（MySQL）やWebアプリがportをLISTENしているはず。  
memcahedやRedisも居るかも。結果や不明点を適度にログる。  
~/webappのディレクトリ構成を調べ必要に応じ/etc, var/logの様子も確認。

### ■環境保全とCICD準備
isucon13f1を代表としてgithubのプライベートリポジトリへpushし環境保全する。
- [ ] /etcから主要なアプリ設定を~/webapp/etcにコピー。（nginx,mysqlなど。systemdあたりも？）
- [ ] リモートリポジトリ登録して初回push。05_add_webapp_to_github.shを改変して実行、または[ここ](20231019_webapp_to_github.md)を参考に手動で設定する。
- [ ] 他のインスタンスでpullしてコンフリクトがないことを確認する。

### ■サーバ環境設定
以後の作業のため環境設定を行う。
```
$ sudo apt -y install dstat             # dstat
$ sudo apt -y install jq                # jq
# prometheus; http://{IP}:9090/ or curl localhost:9090/metrics --> AWSの9090ポートを開けること
$ sudo apt -y install prometheus prometheus-node-exporter
# alp
$ wget https://github.com/tkuchiki/alp/releases/download/v1.0.18/alp_linux_amd64.tar.gz
$ tar xvzf alp_linux_amd64.tar.gz
$ mv alp /usr/local/bin/alp
$ sudo apt -y install apache2-utils     # ab
```
#### nginxのlogのjson化設定
[ここ](20230926_nginx_jsonLog.md)などを参考に作業。

#### /var/logアクセス性改善
/var/logなどの各種ログを見えるようにadmグループに各ユーザーを追加する。下記を参考に編集。  
```
$ sudo vigr -s
- adm:x:4:syslog,ubuntu
+ adm:x:4:syslog,ubuntu,isucon,hidetake,seigot,maleicacid
+ adm:x:4:syslog,ubuntu,isucon,kiwasa,takaaki,miteru
```
他にもisucon,webapp,mysql等のグループが存在して作業の都合が良ければ必要に応じユーザ追加する。

### ■サーバ動作確認
アプリケーションマニュアルを参照しつつブラウザでアクセスして動作を把握する。

### ■初回ベンチマーク
logrotateしてからベンチマーク実施。

## 【攻略】
### ■RDB攻略
- USER/PASSを確認しログイン。
- DBとテーブルの調査。（テーブル名、各テーブル行数・バイト数、テーブル定義、インデックスを確認し調査表に書き出し。）
- 初期化データの有無を確認。無ければこの時点でmysqldump実施。
- [ここ](20231005_mysql_slowlog.md)を参考にslowlogをオン（競技終了時にはoff）
### ■WebApp攻略
- alpの実行
- アプリログの場所の確認、内容の確認
- WebAPIのリストアップ
- N+1の特定と対策
- その他の重くて不要な処理の確認
- キャッシュの検討
### ■HTTPサーバ周辺攻略
- staticコンテンツの取得状況確認
- nginx.conf他の設定の見直し

### ■CI/CD
- 各ユーザごとのブランチで改変しpull,commit,push（クライアント端末が作業しやすい）
- 各自のインスタンスでベンチして問題なさそうならmainにマージ

## 【競技終了】
17:00 リーダーボードの更新停止
### ■最終動作確認(17:00-18:00)
- slowlog off、prometheusサービス停止
- RDBデータ初期化、サービス再起動、再起動試験
- 最終ベンチ
- 18:00 競技終了、ログアウト

### ■結果発表(19:30)

## 備考

## リンク
[ISUCON13 レギュレーション : ISUCON公式Blog](https://isucon.net/archives/57768216.html)  
[ISUCON13 Portal : Teamページ](https://portal.isucon.net/auth/settings/team/)  
[ISUCON13 Portal :クラウド利用クーポン](https://portal.isucon.net/auth/settings/cloud_coupon/)  
[ISUCON13 New Relic 支援プログラム](https://newrelic.com/jp/blog/nerd-life/isucon13)  
