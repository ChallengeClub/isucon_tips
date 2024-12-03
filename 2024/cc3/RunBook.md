# ISUCON14 本戦RUNBOOK
[Portal](https://portal.isucon.net/)  
[参加規約](https://isucon.net/archives/58657108.html)  
[レギュレーション](https://isucon.net/archives/58657116.html)   

## 【前日までの準備】
- [x] cc3チーム登録（いわさ）
- [x] 競技環境確認（ポータルから試験用のCloudFormation実施/試験ssh接続）  
- [x] メンバ全員の登録（ゆんたんさん、tkさん）、Discord参加、githubのssh公開鍵登録
- [x] Discordグループ作成
- [x] AWSクーポン入手とAWSへの登録
- [ ] 当日用のPrivateリポジトリ準備（tkさん、ゆんたんさんを招待）
  - https://github.com/iwatadive28/isucon14_cc3f1/settings
- [ ] 各自の攻略環境用意（o11yリポジトリを元にしたpprotein可視化環境／CICD環境。github codespaces推奨。ssh秘密鍵登録しよう。.bashrcでssh-agent登録推奨。）
- [ ] 攻略用のPrivareリポジトリ用意
- [ ] お昼ごはん、おやつ、ドリンク、睡眠  

## 【当日競技開始】
> **Info:** 競技日程: 2024年12月8日（日）　競技時間: 10:00 - 18:00（JST）  
運営が事前発表する競技当日の流れを読んでおき、当日に発表する本戦当日マニュアルを読む。  
isucon14 Discordは都度確認する。

![hight:100](../images/system_setup.dio.svg)

### 開始~ISUCON14デフォルト環境構築

- [ ] 当日マニュアル確認(環境構築と並行して分担しても良い)
- [ ] [ISUCON14 Portal](https://portal.isucon.net)からCloudFormationのテンプレートをダウンロード、ip address確定。
- [ ] ダウンロードしたテンプレートファイルを元にAWSでスタックを作成しCREATE_COMPLETEを待つ。(EIPの上限5に注意)
- [ ] .ssn/config設定、EC2ログイン試験(user=isucon)
  - [ ] ~/binを作成しisucon_toolsをgit cloneする。
  - [ ] 04_setupSSH.shを実行してssh keepalive設定を行う。  

EC2上で以下実行
```
$ cd ~
$ mkdir bin
$ cd bin
$ git clone https://github.com/ChallengeClub/isucon_tools.git
$ cd isucon_tools/
$ ./04_setupSSH.sh
ClientAliveInterval を 30 秒に設定しました。
パスワードによるSSHログインが無効化されました。
```

各自の秘密鍵を `~/.ssh/` へ置き、権限を変更。
```bash
$ chmod 600 ~/.ssh/isucon13.pem
$ ls -al ~/.ssh | grep isucon13.pem
-rw-------  1 codespace codespace 1674 Nov 12 12:27 isucon13.pem
```

各自の開発環境上のsshconfigを設定。(~/.ssh/config)
```bash
$ sudo nano ~/.ssh/config
Host isucon13 
    User ubuntu # isucon Userでログインするようにするべき？
    HostName <ip-address>
    Port 22
    IdentityFile ~/.ssh/isucon13.pem
    ForwardAgent yes
```

  - [ ] 必要なメンバーはVSCodeRemoteDevelopの接続等を設定(autoscanは必ずoffで)
- [ ] ブラウザから対象サービス利用開始
- [ ] ポータルから初回ベンチマーク実行（Discordへログをレポート）

### サーバー内部調査
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

ローカル環境のIPアドレスの確認方法。
[Local]
```bash
$ curl httpbin.org/ip
{
  "origin": "23.97.62.119"
}
```
セキュリティグループのインバウンドルールに追加する。

![image](https://github.com/ChallengeClub/isucon_tips/raw/main/2024/images/2024-11-12-AWS-PortSetting.png)

### 環境保全とCICD準備
isucon14f1を代表としてソースや設定をgithubのプライベートリポジトリへpushし環境保全する。  
※やりかたは色々ありますのでこれから詳細錬成予定。scriptやsnipetで補助しつつ基本手動で。

#### コード管理
- [ ] /etcから主要な設定を~/webapp/etcにコピー。（nginx,mysql, systemdなど）

EC2上、isuconユーザーで扱う前提。
```
$ cp -r /etc/mysql webapp/mysq$
$ sudo cp -r /etc/mysql webapp/mysql
```

##### 1.webappをローカルにコピーして保存する方法

- webappのファイルサイズ確認
```bash
$ du -h -d 1
128K    ./nginx
92K     ./mysql
38M     ./php
6.4M    ./go
787M    ./rust
108M    ./node
84K     ./pdns
112K    ./python
48M     ./perl
60K     ./ruby
3.8M    ./sql
2.4M    ./public
263M    ./.git
12K     ./img
1.3G    .
```
上の内容であれば、node と rust が大きいので削除する。

```bash
$ cd webapp
$ rm -r node
$ cd rust
$ cargo clean
     Removed 2778 files, 955.5MiB total
```

webappを圧縮。
[EC2]
```bash
$ cd ~
$ tar czvf webapp.tgz webapp
```

webappをEC2からローカル環境にコピーして解凍する。
[Local]
```
$ scp -i ~/.ssh/isucon13.pem ubuntu@52.68.122.251:/home/isucon/webapp.tgz ./
$ tar -xzvf webapp.tgz
$ rm webapp.tgz
```
この状態でgit 管理する。

[Local]
```
$ git add webapp
$ git commit -m 'add webapp from isucon*'
$ git push origin [isucon13_practice] # ブランチ名
```

##### 2.本番環境上でwebappをgit管理する方法
(未検証、昨年はこの方法で管理しました)

- [ ] webappでgit initして空commit、.gitignoreを作成しgit add,commit
- [ ] リモートリポジトリ登録して初回push。05_add_webapp_to_github.shを改変して実行。または[ここ](https://github.com/ChallengeClub/isucon_tips/blob/main/2023/20231019_webapp_to_github.md)を参考に手動で設定。
- [ ] 他のインスタンスでpullしてコンフリクトがないことを確認する。(手順未確認)

#### CICDフロー構築
※ 素振り会[20241112_ISUCON13モニタリングツール起動からベンチマークまで](https://github.com/ChallengeClub/isucon_tips/blob/main/2024/20241112_ISUCON13%E3%83%A2%E3%83%8B%E3%82%BF%E3%83%AA%E3%83%B3%E3%82%B0%E3%83%84%E3%83%BC%E3%83%AB%E8%B5%B7%E5%8B%95%E3%81%8B%E3%82%89%E3%83%99%E3%83%B3%E3%83%81%E3%83%9E%E3%83%BC%E3%82%AF%E3%81%BE%E3%81%A7.md)参照。

##### 可視化ツールの設定ファイル修正
- [ ] ansible/inventory.yaml
isucon13 EC2はインスタンスが一つであるため、以下のように修正。
```
all:
  hosts:
    server1:
      ansible_host: [IP]
      ansible_user: ubuntu
```

- [ ] pprotein/data/targets.json
サーバーのIPアドレスを変更。
```
[
  {
    "Type": "pprof",
    "Label": "web",
    "URL": "http://[IP]:8080/debug/pprof/profile",
    "Duration": 70
  },
  {
    "Type": "httplog",
    "Label": "nginx",
    "URL": "http://[IP]:19000/debug/log/httplog",
    "Duration": 70
  },
  {
    "Type": "slowlog",
    "Label": "mysql",
    "URL": "http://[IP]:19000/debug/log/slowlog",
    "Duration": 70
  }
]
```

- (任意) ansible/roles/mysql/files/etc/mysql/mysql.conf.d/mysqld.cnf
基本的にはISUCON13のサーバーから持ってきて、log出力部のみ追記する。他にボトルネックがない前提ですが、SlowLogがパフォーマンスに影響を与えるため、コンテスト終盤ではSlowLog出力をせずに最高スコアを狙うことも考えられる。

- (任意) ansible/roles/nginx/files/etc/nginx/nginx.conf
基本的にはISUCON13サーバーから持ってきて、Logging Settingを修正する。※ ISUCON本60pでは、アクセスログをjson形式で出力している。

##### Ansibleの起動
CodeSpace上で以下実行。
[Local] 
```bash
$ cd ansible
$ ansible-playbook -i inventory.yaml setup_targets.yaml --private-key ~/.ssh/isucon13.pem
```

##### 可視化用の各種サーバーの起動
CodeSpace上で以下を実行。
```
$ docker compose up -d
```
pprotainへのアクセスしてモニタリングできるようになっているはず。
（CodeSpaceで"ポート"タブ -> 9000のアドレスを開く。）

![image](https://github.com/ChallengeClub/isucon_tips/blob/main/2024/images/2024-11-12-CodeSpace-pprotain.png)

#### Webappのビルド&デプロイ
ローカル環境でビルドして、生成されたバイナリをEC2にデプロイする。

Go環境
[Local] コードスペース
```bash
$ cd webapp/go
$ make
```

- デプロイ方法は要確認
- デプロイ方法によって、依存関係に注意する必要あり。参照（https://www.elastiflow.com/blog/posts/disabling-cgo-to-remove-glibc-dependency）。
1. ビルド → コピーの時
1. コピー → ビルドの時

# 以下、編集予定 from ひでたけさんメモから参照

--- 
- [ ] CICDフロー構築
  - [ ] inventory.yaml設定、ansible接続試験（test_connection.yaml）
  - [ ] インスタンスのwebapp(/etcのコピー含む)をisucon14fへgit登録（直接pushでも手元環境へコピーしてpushでもOK）
  - [ ] 各自の開発環境でisucon14fをpull
  - [ ] ansible環境構築（setup_targets.yaml）、agentサービス起動、slowlogオン、nginxのtsv設定
  - [ ] main.goにpprotein計装、ビルドとデプロイ（build_and_deploy.yaml）、pprotein計測試験
  - [ ] ポータルから第２回ベンチマーク実行（Discordへログをレポート）
  
- Dev/CICD
    - 各自devブランチでwebapp修正、ビルドとデプロイ（build_and_deploy.yaml）
    - ポータルから修正後ベンチマーク実行（Discordへログをレポート）
    - 各自devブランチへcommit/push、プルリクエスト作成(dev->main,ベンチ点数を付記)
    - プルリクエストのマージ
- 最終リリース
    - 各インスタンスのソースコード更新（※goのbuild_and_deploy.yamlで実行ファイルのみ更新している場合。）
    - 計測環境のリバート（agentサービス停止、slowlogオフ。pprotein計装コメントアウト。nginxログのオフ？）
    - 再起動試験(EC2の再起動、ベンチマーク)
