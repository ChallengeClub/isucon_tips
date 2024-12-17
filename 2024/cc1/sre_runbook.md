# ISUCON14 本戦RUNBOOK CC1 SRE用
[Portal](https://portal.isucon.net/)  
[参加規約](https://isucon.net/archives/58657108.html)  
[レギュレーション](https://isucon.net/archives/58657116.html)   
[cc1_o11y：攻略環境](https://github.com/HideakiTakechi/cc1_o11y)  
[cc1_webapp：ISUCON14ソース](https://github.com/HideakiTakechi/cc1_webapp)  
[システム全体図と攻略の概要](https://github.com/HideakiTakechi/cc1_tips/blob/main/2024/system_setup.md)

[HideakiTakechi](https://github.com/HideakiTakechi)   [YK-marigold](https://github.com/YK-marigold)   [Eri5yn4ck](https://github.com/Eri5yn4ck)  

## 【事前準備】
- [x] cc1チーム登録（ひでたけ）
- [x] 競技環境確認（ポータルから試験用のCloudFormation実施/試験ssh接続）  
- [x] メンバ全員の登録（よーこさとう）、Discord参加、githubのssh公開鍵登録
- [x] AWSクーポン入手とAWSへの登録
- [x] Discordグループ作成
- [x] 攻略環境用意（o11yリポジトリを元にしたpprotein可視化環境／CICD環境）
- [x] 攻略用のPrivareリポジトリ用意
- [x] github codespacesの作成、ssh秘密鍵登録。.bashrcでssh-agent登録
- [x] お昼ごはん、おやつ、ドリンク、睡眠  

## 【当日競技開始】
> **Info:** 競技日程: 2024年12月8日（日）　競技時間: 10:00 - 18:00（JST）  
運営が事前発表する競技当日の流れを読んでおき、当日に発表する本戦当日マニュアルを読む。  
isucon14 Discordは都度確認する。    

### ■EC2の起動
SREが以下の作業を行う。
- [x] [ISUCON14 Portal](https://portal.isucon.net)からCloudFormationのテンプレートをダウンロード。  
- [x] ダウンロードしたテンプレートファイルを元にAWSでスタックを作成しCREATE_COMPLETEを待つ。(EIPの上限5に注意)  
- [x] 全インスタンスのIPアドレスをDiscordで連絡する。
- [x] 各インスタンスに~/bin/isucon_toolsを導入しssh keepalive設定などを行う。

### ■ssh接続準備  
- [x] .ssh/configへ全インスタンスのIPアドレスを追記する。(ForwardAgent=yesでssh-agentもONにしよう)　
- [x] 出来たインスタンスに各自の攻略環境からssh接続する。user=isuconで接続できるはず。
- [x] ~/binを作成しisucon_toolsをgit cloneする。
- [x] 04_setupSSH.shを実行してssh keepalive設定を行う。  
```
Host isucon14f1
    User isucon
    HostName <ip-address>
    Port 22
    IdentityFile ~/.ssh/isucon14.pem
    ForwardAgent yes
```
```
$ ssh isucon14f1
$ cd ~
$ mkdir bin
$ cd bin
$ git clone https://github.com/ChallengeClub/isucon_tools.git
$ cd isucon_tools/
$ ./04_setupSSH.sh
```
### ■Ansible接続準備  
- [x] ansibleのinventory.yamlに全インスタンスのIPアドレス追記する。
- [x] EC2への接続試験を行う。
```
$ cd ansible
$ vi inventory.yaml
$ ansible-playbook -i inventory.yaml test_connection.yaml # EC2へのssh接続試験
```
### ■EC2にssh接続
- [x] ~/binを作成しisucon_toolsをgit cloneする。
- [x] 04_setupSSH.shを実行してssh keepalive設定を行う。  
```
$ cd ~
$ mkdir bin
$ cd bin
$ git clone https://github.com/ChallengeClub/isucon_tools.git
$ cd isucon_tools/
$ ./04_setupSSH.sh
```

### ■EC2環境保全（webapp）
用意しておいたgithubのプライベートの空リポジトリ[cc1_webapp](https://github.com/HideakiTakechi/cc1_webapp)にwebappを登録する。
isucon14f1を代表としてソースや設定をpushし環境保全する。  
※scriptやsnipetで補助しつつ基本手動で。 
- [x] EC2に接続しwebapp/.gitigonoreを設定。
- [x] webappでgit initして空commit、.gitignoreを作成しgit add,commit
- [x] リモートリポジトリ登録して初回push。05_add_webapp_to_github.shを改変して実行。または[ここ](https://github.com/ChallengeClub/isucon_tips/blob/main/2023/20231019_webapp_to_github.md)を参考に手動で設定。
- [ ] 他のインスタンスでpullしてコンフリクトがないことを確認する。
```
$ cd ~/webapp
$ du -h --max-depth=1                     # フォルダ容量確認
$ vi .gitignore                           # 不要なものをignoreする
$ git init
$ git remote add origin git@github.com:HideakiTakechi/isucon13f_cc1.git
$ git config --global user.name "isucon"
$ git config --global user.email "isucon@example.com"
$ git commit --allow-empty -m "initial commit"
$ git add .
$ git status
$ git commit -m "add webapp"
$ git push -u origin main
```
または以下でも良い。
```
$ cd ~/bin
$ vi 06_add_webapp_to_github_gitpull.sh   # configやremote urlを編集
$ ./06_add_webapp_to_github_gitpull.sh    # webapp以下をgithubに登録する。
```
### ■EC2環境保全（etc）
- [x] /etcから主要な設定を~/webapp/etcにコピー。（nginx,mysql,systemdなど）
- [x] commit,push
```
$ cd ~/webapp
$ mkdir etc
$ cd /etc
$ ls
$ du -h --max-depth=1 | grep -E "systemd|mysql|nginx"
$ sudo cp -r nginx /home/isucon/webapp/etc
$ sudo cp -r mysql /home/isucon/webapp/etc
$ sudo cp -r systemd /home/isucon/webapp/etc
$ cd ~/webapp
$ git add .
$ git commit -m 'copy from /etc/nginx,mysql,systemd'
$ git push
```

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

#### ポートの開け方
EC2→セキュリティグループ->インバウンドルールの追加で変更できます。

### ■サーバ動作確認
アプリケーションマニュアルを参照しつつブラウザでアクセスして動作を把握する。

## 【攻略】
### ■RDB攻略
- USER/PASSを確認しログイン。
- DBとテーブルの調査。（テーブル名、各テーブル行数・バイト数、テーブル定義、インデックスを確認し調査表に書き出し。）
- 初期化データの有無を確認。無ければこの時点でmysqldump実施。★
- [ここ](20231005_mysql_slowlog.md)を参考にslowlogをオン（競技終了時にはoff）
### ■WebApp攻略
- pproteinの実行(pprof/http/slowlog)
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
- slowlog offなどサービス停止
- RDBデータ初期化、サービス再起動、再起動試験
- 最終ベンチ
- 18:00 競技終了、ログアウト

### ■結果発表(20:00)
