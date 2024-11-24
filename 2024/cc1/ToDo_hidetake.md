# ISUCON14攻略ToDo

## 【スケジュール】
- [x] 11/21 もくもく会、環境構築（AnsibleでAWS EC2に接続して動かす。）
- [ ] 11/26 素振り会、チーム登録、作った環境を使ってチームで点数アップ演習（皆で加点要素を試す。）
- [ ] 11/28 もくもく会、環境整備（Ansible/pprof/webapp/nginx/mysqlで動くもの。構築手順確立。）
- [ ] 12/3  素振り会、環境を使ってチームで点数アップ演習（github経由でマージ）
- [ ] 12/5  もくもく会、環境整備（フル動作済み。構築手順整備。出来たらnginx/SQL設定替えなどの加点要素。）
- [ ] 12/7　前日演習戦(模擬演習(3h)、必須加点要素クリア確認(SQL/N+1) )
- [ ] 12/8  本戦当日

## 【参加準備と手配】
- [x] cc1チーム登録（ひでたけ）
- [x] 競技環境確認（ポータルから試験用のCloudFormation実施/試験ssh接続）  
- [ ] メンバ全員の登録（よーこさとう）、Discord参加、githubのssh公開鍵登録
- [ ] AWSクーポン入手
- [ ] Discordグループ作成
- [ ] 攻略用のPrivareリポジトリ用意
- [ ] 各自の攻略環境用意（pprotein可視化環境／CICD環境。ssh秘密鍵登録。github codespaces推奨。）
- [ ] お昼ごはん、おやつ、ドリンク、睡眠

## ■ISUCON本攻略チェックリスト（Action込みメモ）
```
	□１章　基礎
		□ top
		□ ベンチマーク
	□２章　モニタリング
		□ stress -c 1
		□ node_expoter(prometeus)
	□３章　負荷試験
		□  nginxのjsonログ
		□ alp
		□ ab
		□ log rotate
		□ slow queryログ(mysqldumpslow)
		□ mysql接続, EXPLAIN, ADD INDEX
		□ dstat
	□４章　シナリオ試験
		□ k6
	□５章　データベース
		□ SHOW PLOCESSLIST
		□ pt-query-digest
		□ query-digester
		□ ADD FULLTEXT INDEX
		□ N+1問題
		□ memcached
	□６章　リバースプロキシ
		□ 静的ファイル配信
```
## ■環境や攻略のヒント
- [pprotein でボトルネックを探して ISUCON で優勝する](https://zenn.dev/team_soda/articles/20231206000000)
- [ISUCONチートシートv2022 公開版](https://hackmd.io/@to-hutohu/isucon2022)

## ■IUSCON13解説・攻略に沿った攻略
- [ISUCON13 問題の解説と講評(公式)](https://isucon.net/archives/58001272.html)
- [ISUCON13 関連エントリまとめ(公式)](https://isucon.net/archives/57991509.html)
- [ISUCON13に参加して4位になりました (187,577点)](https://blog.p1ass.com/posts/isucon13/)

## ■IUSCON12予選解説に沿った攻略
- [ISUCON12 予選の解説 (Node.jsでSQLiteのまま10万点行く方法)](https://isucon.net/archives/56842718.html)  
- [ISUCON12 予選問題の解説と講評](https://isucon.net/archives/56850281.html)  
```
	□ visit_historyへのindex追加
	□ visit_historyの不要行の削減(300万→20万行)
```
## ■moさんのisucon-o11y足跡起点
- [isucon-o11y](https://github.com/mo124121/isucon-o11y)　各種可視化ツールの詰め合わせ環境
- [isucon13-try](https://github.com/mo124121/isucon13-try) isucon13を構成管理をものすごい勢いでやるトライアル
- [ISUCON過去問関連の計装に関するメモ書き](https://qiita.com/mo124121/items/d99ca8fb39ed54237e9b)

## ■モブプロでisucon-o11y演習
- [20241112_ISUCON13モニタリングツール起動からベンチマークまで](https://github.com/ChallengeClub/isucon_tips/blob/main/2024/20241112_ISUCON13%E3%83%A2%E3%83%8B%E3%82%BF%E3%83%AA%E3%83%B3%E3%82%B0%E3%83%84%E3%83%BC%E3%83%AB%E8%B5%B7%E5%8B%95%E3%81%8B%E3%82%89%E3%83%99%E3%83%B3%E3%83%81%E3%83%9E%E3%83%BC%E3%82%AF%E3%81%BE%E3%81%A7.md)
- [20241105_pprof](https://github.com/ChallengeClub/isucon_tips/blob/main/2024/20241105_pprof.md)

## ■足掛かりリポジトリ
- [isucon-o11y-isucon13f1](https://github.com/HideakiTakechi/isucon-o11y-isucon13f1) isucon-o11yのfork(cc1起点整備中)
- [isucon13](https://github.com/HideakiTakechi/isucon13) 10/22にAkijinさんが演習構築したもののfork（使わない予定）
- [isucon13f3](https://github.com/HideakiTakechi/isucon13f3) 11/19にスクラッチで作成したisucon13 webappリポジトリ
- [isucon_tools](https://github.com/ChallengeClub/isucon_tools) CICD自動化前に個別ツールが重宝する場面で適宜使おう。

## ■作業フロー
- 鍵ペアの準備
    - [x] isucon14用の鍵ペア作成、githubへ登録（ssh用/git push用）、AWSへ登録（練習時のubuntuのssh用）
- 攻略用のCodespaces準備
    - [x] isucon13-o11yをフォーク　⇒　[isucon-o11y-isucon13f1](https://github.com/HideakiTakechi/isucon-o11y-isucon13f1)
    - [x] フォークしたリポジトリからcodespaces作成　⇒　[cc1-isucon13-try](https://fantastic-couscous-4jwj7vvwpjghj445.github.dev/)
    - [x] codespacesに先の鍵ペアを配置。(ssh-agentを起動してssh-addしておくと接続時に鍵の指定が不要になるのでお薦め。)
    - [x] ついでにhttpbin.orgでcodespacesのソースIPアドレスも調べておこう。
```
$ mkdir ~/.ssh
$ vim ~/.ssh/id_ed25519.pub
$ vim ~/.ssh/id_ed25519
$ chmod 600 ~/.ssh/id_ed25519
$ stat -c "%n %a" ~/.ssh/*
/home/codespace/.ssh/id_ed25519 600
/home/codespace/.ssh/id_ed25519.pub 644
$ eval "$(ssh-agent -s)
$ ssh-add ~/.ssh/id_ed25519
$ curl httpbin.org/ip
```
- EC2インスタンスを起動して接続
    - [x] EC2インスタンスに接続。(本戦はuser=isuconで接続できる。練習時はuser=ubuntuで接続する必要がある。)
    - [x] codeapacesの~/.ssh/configにEC2全インスタンスのIPアドレス追記しておくのがお薦め。
    - [x] ~/binを作成しisucon_toolsをgit cloneする。
    - [x] ./04_setupSSH.shを実行してssh keepalive設定を行う。
    - [x] ./07_add_github_keys.shを実行してuser=isuconでssh接続できるようにする。（本番では不要）  
```
$ ssh -l ubuntu ip_address
$ sudo su isucon -
$ cd
$ mkdir bin
$ cd bin
$ git clone https://github.com/ChallengeClub/isucon_tools.git
$ git remote set-url origin git@github.com:ChallengeClub/isucon_tools.git
$ cd isucon_tools/
$ ./04_setupSSH.sh
$ ./07_add_github_keys.sh HideakiTakechi
``` 
- CodespacesからEC2を計測する環境を整備
    - [x] codeapacesのinventory.yamlを修正。(ansible_host: ip_addressを記載)
    - [x] ansibleでssh接続試験(test_connection.yamlでwebservers(web1,web2)にpingを行う。)
    - [x] ansibleでsetup_targets.yamlを実行してEC2に計測環境を準備する
        - [x] agentサービス(pprotein-agent,node_exporter,process-exporter）をインストール
        - [x] MySQL設定(Slowlogをオン)
        - [x] nginx設定(log formatのtsv化)
    - [x] EC2のセキュリティグループのinboundにcodespacesのipアドレスからの許可を追加しておこう。(pprotein-agent,node_exporter,process-exporterなどが使う)
```
$ cd ansible
$ vi inventory.yaml
$ ansible-playbook -i inventory.yaml test_connection.yaml # EC2へのssh接続試験
$ ansible-playbook -i inventory.yaml setup_targets.yaml --tags deploy_agents # agent設定のみ個別適用する場合
$ ansible-playbook -i inventory.yaml setup_targets.yaml # 全部のタスクを適用する場合
``` 
- 用意しておいたgithubの空リポジトリにwebappを登録する。
    - [x] EC2に接続しwebapp/.gitigonoreを設定。
    - [x] webappをgithubに登録。---> [HideakiTakechi/isucon13f3](https://github.com/HideakiTakechi/isucon13f3)
```
$ ssh -l isucon ip_address
$ cd webapp
$ du -h --max-depth=1                     # フォルダ容量確認
$ vi .gitignore                           # 不要なものをignoreする
$ git clone/config/add/commit/pushで空リポジトリにwebappを登録する。
```
- codespacesでwebappのCICD準備とpprof計装
    - [x] codespacesにwebappをclone。
    - [x] webappのmain.goにpprofの計装を追加。ビルドに必要なgoモジュールを導入。
    - [x] WebappのBuild and Deployスクリプトを実施。
```
$ git clone git@github.com:HideakiTakechi/isucon13f3.git
$ mv isucon13f3 webapp
$ cd webapp/go
$ vi main.go
$ go mod tidy                              # moduleの導入。module追記時のみ。
$ ansible-playbook -i inventory.yaml build_and_deploy.yaml
```
- 計測
    - [x] codespacesでpprotein環境を起動しWebコンソール画面を表示。
    - [x] EC2でBuild/Deploy/再起動が成功しているか確認
    - [x] EC2でベンチ実施し、pproteinのWebで計測。(計測開始はcollectボタンを押す。現在70秒間計測する設定。)
    - [x] codespacesのpproteinのWeb画面で結果表示。
```
cs $ docker-compose up -d　　　　　　　　# codespacesでpprotain環境を起動。port:9000でWebコンソールが起動する。
cs $ vi pprotein/data/targets.json　　　# pprotainが測定する先のEC2 ip adrressを設定。（リロードで反映出来た）
ec2 $ systemctl status isupipe-go      # Build/Deploy/サービス再起動が成功したか確認
ec2 $ ./bench run --enable-ssl         # ベンチ実行。事前確認に30秒ほどかかる。
```
- [ ] cc1版CICDベンチ環境の動作確認。
- [ ] 必要に応じプルリクを送る。
- [ ] isucon13版のcloudformationのyamlを作成。
- [ ] cloudformationでインスタンスを作成してcodespaceから接続。
- [ ] 攻略・点数アップ（まずはindex追加から）
