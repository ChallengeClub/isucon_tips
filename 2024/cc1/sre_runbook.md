# ISUCON14 本戦RUNBOOK CC1 SRE用
[Portal](https://portal.isucon.net/)  
[参加規約](https://isucon.net/archives/58657108.html)  
[レギュレーション](https://isucon.net/archives/58657116.html)   

## 【事前準備】
- [x] cc1チーム登録（ひでたけ）
- [x] 競技環境確認（ポータルから試験用のCloudFormation実施/試験ssh接続）  
- [x] メンバ全員の登録（よーこさとう）、Discord参加、githubのssh公開鍵登録
- [x] AWSクーポン入手とAWSへの登録
- [x] Discordグループ作成
- [x] 攻略環境用意（o11yリポジトリを元にしたpprotein可視化環境／CICD環境）
- [x] 攻略用のPrivareリポジトリ用意
- [ ] github codespacesの作成、ssh秘密鍵登録。.bashrcでssh-agent登録
- [ ] お昼ごはん、おやつ、ドリンク、睡眠  

## 【当日競技開始】
> **Info:** 競技日程: 2024年12月8日（日）　競技時間: 10:00 - 18:00（JST）  
運営が事前発表する競技当日の流れを読んでおき、当日に発表する本戦当日マニュアルを読む。  
isucon14 Discordは都度確認する。    

### ■起動
以下の作業を行う。
- [ ] [ISUCON14 Portal](https://portal.isucon.net)からCloudFormationのテンプレートをダウンロード。  
- [ ] ダウンロードしたテンプレートファイルを元にAWSでスタックを作成しCREATE_COMPLETEを待つ。(EIPの上限5に注意)  

### ■接続
同一インスタンスが３インスタンス作成される前提で各自の作業用に１インスタンスを使う想定にしましょう。  
- [ ] ansibleのinventory.yamlに全インスタンスのIPアドレス追記する。
- [ ] .ssh/configへ全インスタンスのIPアドレス追記するのがお薦め。(ForwardAgent=yesでssh-agentもONにしよう)　
- [ ] 出来たインスタンスに各自の攻略環境からssh接続する。user=isuconで接続できるはず。  
- [ ] ~/binを作成しisucon_toolsをgit cloneする。
- [ ] 04_setupSSH.shを実行してssh keepalive設定を行う。  
```
$ cd ~
$ mkdir bin
$ cd bin
$ git clone https://github.com/ChallengeClub/isucon_tools.git
$ cd isucon_tools/
$ ./04_setupSSH.sh
```
```
Host isucon13f1
    User isucon
    HostName <ip-address>
    Port 22
    IdentityFile ~/.ssh/isucon14.pem
    ForwardAgent yes
```
- [ ] 必要なメンバーはVSCodeRemoteDevelopの接続等を設定（autoscanは必ずoffで）  

### ■サーバ内部調査
下記などでインスタンスの概要調査を行う。  
```
$ cat /etc/os-release                   # os確認  
$ grep -v nologin /etc/passwd    # user確認  
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
memcahedやRedisも居るかも。調査結果や不明点を適度にログる。（ログ先は必ずprivateに！isucon_tipsにあげちゃダメ！）  
~/webappのディレクトリ構成を調べ必要に応じ/etc, var/logの様子も確認。  
goのサービス名やファイル構成がisucon13(isupipe)どの程度違うか調べてAnsibleに反映/錬成する。  

### ■環境保全とCICD準備
isucon14f1を代表としてソースや設定をgithubのプライベートリポジトリへpushし環境保全する。  
※やりかたは色々ありますのでこれから詳細錬成予定。scriptやsnipetで補助しつつ基本手動で。  
- [ ] /etcから主要な設定を~/webapp/etcにコピー。（nginx,mysql, systemdなど）
- [ ] webappでgit initして空commit、.gitignoreを作成しgit add,commit
- [ ] リモートリポジトリ登録して初回push。05_add_webapp_to_github.shを改変して実行。または[ここ](https://github.com/ChallengeClub/isucon_tips/blob/main/2023/20231019_webapp_to_github.md)を参考に手動で設定。
- [ ] 他のインスタンスでpullしてコンフリクトがないことを確認する。(手順未確認)

```
$ cd ~/webapp
$ du -h --max-depth=1
$ vi .gitignore
$ git init
 ...
```

-----
### 以下2023年版。2024年はcodespacesから作業するので概ね再錬成になるはず。

### ■サーバ環境設定
以後の作業のため環境設定。
```
$ sudo apt -y install dstat             # dstat
$ sudo apt -y install jq                # jq
# prometheus; http://{IP}:9090/ or curl localhost:9090/metrics --> AWSの9090ポートを開けること
# 呪文:　avg without(cpu) (rate(node_cpu_seconds_total{mode!="idle"}[1m]))
$ sudo apt -y install prometheus prometheus-node-exporter
# alp
$ wget https://github.com/tkuchiki/alp/releases/download/v1.0.18/alp_linux_amd64.tar.gz
$ tar xvzf alp_linux_amd64.tar.gz
$ mv alp /usr/local/bin/alp
$ sudo apt -y install apache2-utils     # ab
# ログ置場準備(ベンチマーク結果等github回収用)
$ cd ~/webapp
$ mkdir log
```
#### ポートの開け方
EC2→セキュリティグループ->インバウンドルールの追加で変更できます。
![image](https://github.com/ChallengeClub/isucon_tips/assets/62125060/4994645e-b4a2-4692-8456-817a880e4c6f)

#### nginxのlogのjson化設定
[ここ](20230926_nginx_jsonLog.md)などを参考に作業。

#### /var/logアクセス性改善
/var/logなどの各種ログを見えるようにadmグループに各ユーザーを追加する。下記を参考に編集。  
```
$ sudo vigr -s
- adm:x:4:syslog,ubuntu
+ adm:x:4:syslog,ubuntu,isucon,hidetake,seigot,maleicacid,kiwasa,takaaki,miteru
```
他にもisucon,webapp,mysql等のグループが存在して作業の都合が良ければ必要に応じユーザ追加する。

### ■サーバ動作確認
アプリケーションマニュアルを参照しつつブラウザでアクセスして動作を把握する。

### ■初回ベンチマーク
sudo logrotate -f /etc/logrotate.confしてからベンチマーク実施。

## 【攻略】
### ■RDB攻略
- USER/PASSを確認しログイン。
- DBとテーブルの調査。（テーブル名、各テーブル行数・バイト数、テーブル定義、インデックスを確認し調査表に書き出し。）
- 初期化データの有無を確認。無ければこの時点でmysqldump実施。★
- [ここ](20231005_mysql_slowlog.md)を参考にslowlogをオン（競技終了時にはoff）
### ■WebApp攻略
- alpの実行
- アプリログの場所の確認、内容の確認（journaldで集めている場合下記で確認できる）
```
journalctl -xef -u <サービス名:isuportsなど>
```
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
