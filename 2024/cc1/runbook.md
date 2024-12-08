# ISUCON14 本戦RUNBOOK CC1 
[Portal](https://portal.isucon.net/)  
[参加規約](https://isucon.net/archives/58657108.html)  
[レギュレーション](https://isucon.net/archives/58657116.html)   
[cc1_o11y：攻略環境](https://github.com/HideakiTakechi/cc1_o11y)  
[cc1_webapp：ISUCON14ソース](https://github.com/HideakiTakechi/cc1_webapp)  
[システム全体図と攻略の概要](https://github.com/HideakiTakechi/cc1_tips/blob/main/2024/system_setup.md)

## 【事前準備】
- [ ] お昼ごはん、おやつ、ドリンク、睡眠  
- [ ] Privateリポジトリへの招待３つを承諾する。(cc1_tips/cc1_o11y/cc1_webapp)
- [ ] github codespaces環境を起動する。（ [cc1_o11y](https://github.com/HideakiTakechi/cc1_o11y) でcreate code spaceする。）
- [ ] ~/.ssh/isucon14.pem(やid_rsaなど)にssh秘密鍵を保存する。
```
$ mkdir ~/.ssh
$ vim ~/.ssh/isucon14.pub       # 公開鍵を保存
$ vim ~/.ssh/isucon14.pem        # 秘密鍵を保存
$ chmod 600 ~/.ssh/isucon14.pem  # 安全なPermissionにする
$ stat -c "%n %a" ~/.ssh/*     # Permissionを確認
/home/codespace/.ssh/isucon14.pem 600
/home/codespace/.ssh/isucon14.pub 644
```
- [ ] .bashrcに以下を追記する。
```
# SSHエージェントの自動起動
if [ -z "$SSH_AGENT_PID" ]; then
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/isucon14.pem   # 必要な秘密鍵を追加
fi
```
```
$ vim ~/.bashrc    # 上記の追記
$ ssh-add -l       # 新しいTerminalを開いて鍵登録されていることを確認
```

## 【競技開始】
> **Info:** 競技日程: 2024年12月8日（日）　競技時間: 10:00 - 18:00（JST）  
運営が事前発表する競技当日の流れを読んでおき、当日に発表する本戦当日マニュアルを読む。  
isucon14 Discordは都度確認する。可能ならOBS Studioで録画する。    
[ライブ中継](https://www.youtube.com/live/sT_9E0pTlns)
- 9:30 配信スタート  
- 9:40-10:00 オープニング / 問題の説明  　　　　　　　※ISUCONボイスチャット：ここまではPublicでOK。
- 10:00-18:00 競技時間　　　　　　　　　　　　　　　　※グループチャット：選手は10-18時は大会に関する発言をしない予定。  
- 18:00-19:20 振り返り/ 問題解説 / スポンサープレゼン   
- 20:00 結果発表  
- 20:30 終了予定  

### ■EC2の起動
SREが以下の作業を行う。
- [ ] [ISUCON14 Portal](https://portal.isucon.net)からCloudFormationのテンプレートをダウンロード。  
- [ ] ダウンロードしたテンプレートファイルを元にAWSでスタックを作成しCREATE_COMPLETEを待つ。(EIPの上限5に注意)  
- [ ] 全インスタンスのIPアドレスをDiscordで連絡する。
- [ ] 各インスタンスに~/bin/isucon_toolsを導入しssh keepalive設定などを行う。

### ■ssh接続準備  
- [ ] .ssh/configへ全インスタンスのIPアドレスを追記する。(ForwardAgent=yesでssh-agentもONにしよう)　
- [ ] 出来たインスタンスに各自の攻略環境からssh接続する。user=isuconで接続できるはず。
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
```
### ■Ansible接続準備  
- [ ] ansibleのinventory.yamlに全インスタンスのIPアドレス追記する。
- [ ] EC2への接続試験を行う。
```
$ cd ansible
$ vi inventory.yaml
$ ansible-playbook -i inventory.yaml test_connection.yaml # EC2へのssh接続試験
```

### ■webappのソース登録とCICD準備
SREが以下の作業を行う。
- [ ] isucon14f1を代表としてソースや設定をcc1_webapp(privateリポジトリ)にpushし環境保全する。  
- [ ] /etcから主要な設定を~/webapp/etcにコピー。（nginx,mysql,systemdなど）
- [ ] webappでgit initして空commit、.gitignoreを作成しgit add,commit
- [ ] リモートリポジトリ登録して初回push。05_add_webapp_to_github.shを改変して実行。または[ここ](https://github.com/ChallengeClub/isucon_tips/blob/main/2023/20231019_webapp_to_github.md)を参考に手動で設定。
- [ ] 他のインスタンスでもpullしてコンフリクトがないことを確認する。  
- [ ] 計測環境準備（setup_targets.yaml） --> agentサービス起動、slowlogオン、nginxのtsv設定

作業にしばらく時間がかかるので、完了するまで以下などを行う。

### ■調査／ベンチマーク
- [ ] ポータルから初回ベンチマーク実行。Discordへログをレポートする。
- [ ] アプリケーションマニュアルを参照しつつブラウザでアクセスして動作を把握する。
- [ ] サーバ内部調査を行って結果を適宜cc1_tipsに記入しDiscordにポストする。サービス名など確認しよう。
- [ ] USER/PASSを確認しmysqlにログイン。
- [ ] RDBとテーブルの調査。（テーブル名、各テーブル行数・バイト数、テーブル定義、インデックスを確認しレポート。）
- [ ] RDBの初期化データの場所を確認。

#### ●サーバ内部調査
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
memcahedやRedisも居るかも。調査結果や不明点を適度にログる。（ログ先は必ずprivateのcc1_tipsに！isucon_tipsにあげちゃダメ！）  
~/webappのディレクトリ構成を調べ必要に応じ/etc, var/logの様子も確認。  
goのサービス名やファイル構成がisucon13(isupipe)どの程度違うか調べてAnsibleに反映/錬成する。  

### ■webappソースコードのclone
SREがwebappのソース登録を完了したら、各自のcodespacesにcloneする。
```
$ git clone git@github.com:HideakiTakechi/cc1_webapp.git
$ mv cc1_webapp webapp
$ cd webapp
$ git status
$ git remote -v               # clone元の確認
$ git checkout -b hidetake    # 各自の開発用ブランチを作成する
```
## 【攻略】
### ■RDB攻略（まずSLOWログを解析してSQLの改善）
- [ ] 各自devブランチでsql修正しデプロイ（sql.yaml）
- [ ] デプロイ後にポータルからベンチマーク実行しDiscordへ結果ログをレポート。
- [ ] 良さそうならdevブランチへcommit/pushしてcommit idをSREに連絡。
- [ ] SREはコミットをmainに取り込み。(mergeまたはcherry-pick)

### ■WebApp攻略
- SREがWebAPIをリストアップしてpproteinのhttpdで集計できるようにします。
- 遅いWebAPIをなんとかしましょう。pprofとGoのソースから様子を確認。
- N+1の特定と対策
- その他の重くて不要な処理の確認
- キャッシュの検討

### ■HTTPサーバ周辺攻略
- staticコンテンツの取得状況確認
- nginx.conf他の設定の見直し

## 【競技終了】
17:00 リーダーボードの更新停止、のはず。
### ■最終動作確認(17:00-18:00)
- slowlog off、prometheusサービス停止
- RDBデータ初期化(init.sh等)、サービス再起動、EC2の再起動試験、最終ベンチで確認
- 18:00 競技終了、ログアウト

### ■結果発表(20:00)
