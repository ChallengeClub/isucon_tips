# User Snipets

## ユーザ切替  
```
$ sudo su - isucon
```

## 環境調査  
```
$ cat /etc/os-release                     # os確認  
$ grep -v nologin /etc/passwd             # user確認
$ sudo lsof -P -i | grep -v sshd          # process確認
$ sudo ss -tlp | grep <hoge>              # process確認（Well-known portで確認）
$ sudo ss -tlpn | grep <hoge>             # process確認（port番号確認）
$ service --status-all                    # serviceリスト確認
$ systemctl list-unit-files --type=service
$ systemctl status <hoge>                 # service確認
$ du -h --max-depth=1                     # フォルダ容量の確認
$ file <hoge>                             # file素性確認
```

## インストール  
```
$ sudo apt -y install dstat               # dstat
$ sudo apt -y install jq                  # jq
# prometheus; http://{IP}:9090/ or curl localhost:9090/metrics
$ sudo apt -y install prometheus prometheus-node-exporter
# alp
$ wget https://github.com/tkuchiki/alp/releases/download/v1.0.18/alp_linux_amd64.tar.gz
$ tar xvzf alp_linux_amd64.tar.gz
$ mv alp /usr/local/bin/alp
$ sudo apt -y install apache2-utils       # ab
$ sudo yum install epel-release           # (未検証)
```

## ssh Timeout設定  
ssh設定を編集ミスすると２度とインスタンスに入れない場合が有ります。  
`isucon_tools/04_setupSSH.sh`を使うか下記の切戻し可能手順がお薦め。  
```
$ cd /etc/ssh
$ cp sshd_config sshd_config.old          # sshdサーバ設定バックアップ(sshクライアント設定とは別です)
$ vi sshd_config
ClientAliveInterval 30                    # コメントアウトを外してkeepalive秒数を設定
$ sudo service ssh restart                # 再起動で有効化（現在のssh接続は維持されるので切らないこと）  
# 別ターミナルから正常にssh接続出来れば完了
```

## 環境設定  
```
$ host                                    # 確認
$ host <hoge>                             # 設定(isucon13f1等)
# 以下はお好みで（プロンプト色変更）
$ vi ~/.bashrc
export PS1="[\e[1;34m\]\u\[\e[m\]@\[\e[1;36m\]\h\[\e[m\] \[\e[0;32m\]\W\[\e[m\]]\$ "
```

## git登録作業
```
$ ~/webapp$ du -h --max-depth=1          # フォルダ容量確認
$ vi .gitignore                          # 必要ないフォルダを除外
$ git init
$ git commit --allow-empty -m "initial commit"   # 空commit（おまじない）
```
各言語のフォルダに下記.gitignoreを置くと一時ファイルを除外できる。  
[Go用](https://github.com/github/gitignore/blob/main/Go.gitignore) [Rust用](https://github.com/github/gitignore/blob/main/Rust.gitignore) [その他](https://github.com/github/gitignore/tree/main)

## 負荷試験関係 
```
$ stress -c 1                             # 並列度1で負荷試験
$ ab -c 1 -n 10 https://localhost/        # 並列度1で10回アクセス試験
$ alp json --file /var/log/nginx/access.log  # アクセスログ解析 
$ sudo logrotate -f /etc/logrotate.conf   # logrotate
$ cd ~/bench
$ ./bench -target-addr 127.0.0.1:443      # isucon12qベンチマーク
# 画面表示しながらログを残したい場合は下記。（githubにbench_2023-11-21-2211.txtとかのファイルを残せる。）
$ ./bench -target-addr 127.0.0.1:443 | tee ~/webapp/log/bench_$(date +%Y-%m-%d-%H%M).txt   
```

## 負荷確認  
ブラウザで`http://{IPアドレス}:9090/`を開くと、GUIが表示される。
ここで、GUI上部のコンソールに以下を入力し、Excecuteするとグラフが表示される。
以下は、CPUの利用時間を1分ごとに出力するクエリ。
```
avg without(cpu) (rate(node_cpu_seconds_total{mode!="idle"}[1m]))
```

## journalログ確認
```
$ journalctl -xef -u <unit_name>                         # -fで継続表示(follow)  isuportsとか指定してログ確認
$ SYSTEMD_LESS=FRXMK journalctl -eu <unit_name>          # 右端折り返しで表示
```

## 接続確認
```
$ curl -k https://localhost
$ curl -kv https://localhost
```

## Docker
```
$ docker ps -a                            # コンテナの確認
$ docker start <hoge>
$ docker stop <hoge>
$ docker restart <hoge>
$ docker exec -it <hoge> bash             # コンテナへの接続（bashなければsh）
```

## nginx  
```
$ sudo systemctl status nginx             # ステータス
$ sudo systemctl reload nginx             # 設定ファイルのリロード（無切断）
$ sudo nginx -t                           # 設定ファイル確認
$ sudo systemctl restart nginx            # 再起動
$ /usr/sbin/nginx -s reopen               # ログローテートの直接指示
```

### nginxログのjson化

alpで解析可能にするために/etc/nginx/nginx.confを編集する。元からあったaccess_log指定はコメントアウト。 
```
$ vi /etc/nginx/nginx.conf
    :
http {

   log_format json escape=json '{"time":"$time_local",'
                                '"host":"$remote_addr",'
                                '"forwardedfor":"$http_x_forwarded_for",'
                                '"req":"$request",'
                                '"status":"$status",'
                                '"method":"$request_method",'
                                '"uri":"$request_uri",'
                                '"body_bytes":$body_bytes_sent,'
                                '"referer":"$http_referer",'
                                '"ua":"$http_user_agent",'
                                '"request_time":$request_time,'
                                '"cache":"$upstream_http_x_cache",'
                                '"runtime":"$upstream_http_x_runtime",'
                                '"response_time":"$upstream_response_time",'
                                '"vhost":"$host"}';

        access_log /var/log/nginx/access.log json;
中略
       # access_log /var/log/nginx/access.log;
$ sudo nginx -t                           # 設定ファイル確認
$ sudo systemctl restart nginx            # 再起動
$ /usr/sbin/nginx -s reopen               # ログローテート
$ alp json --file /var/log/nginx/access.log
```

## mysql  
```
$ mysql -u isucon -p                     # 接続
mysql> show databases;                   # DB一覧
mysql> use hoge_db;                      # DB接続
mysql> show tables;                      # TABLE一覧
mysql> describe hoge_table;              # TABLE概要
mysql> SHOW FULL PROCESSLIST;            # ベンチ中等に実行中の処理の確認
```

## その他一般
```
echo 'eHh4Cg==' | openssl enc -d -base64     # base64 decode. POSTデータ/フォーム/画像の中身を確認したいときなど。
```
