# User Snipets (hidetake)

## ユーザ切替  
```
$ sudo su - isucon
```

## インストール  
```
$ sudo apt -y install dstat             # dstat
$ sudo apt -y install jq                # jq
# prometheus; http://{IP}:9090/ or curl localhost:9090/metrics
$ sudo apt -y install prometheus prometheus-node-exporter
# alp
$ wget https://github.com/tkuchiki/alp/releases/download/v1.0.18/alp_linux_amd64.tar.gz
$ tar xvzf alp_linux_amd64.tar.gz
$ mv alp /usr/local/bin/alp
$ sudo apt -y install apache2-utils     # ab
$ sudo yum install epel-release         # (未検証)
```

## 環境調査  
```
$ cat /etc/os-release                   # os確認  
$ cat /etc/passwd | grep -v nologin     # user確認  
$ sudo lsof -P -i | grep -v sshd        # process確認
$ sudo ss -tlp | grep hoge              # process確認
$ sudo ss -tlpn | grep hoge             # process確認
$ service --status-all                  # serviceリスト確認
$ systemctl status hoge                 # service確認
$ file hoge                             # file素性確認
```

## 負荷試験関係 
```
$ stress -c 1                           # 並列度1で負荷試験
$ ab -c 1 -n 10 https://localhost/      # 並列度1で10回アクセス試験
$ alp json --file access.log            # アクセスログ解析
$ sudo logrotate -f /etc/logrotate.conf # logrotate
$ cd ~/banch
$ ./bench -target-addr 127.0.0.1:443    # isucon12qベンチマーク
```
## 負荷確認  
ブラウザで`http://{IPアドレス}:9090/`を開くと、GUIが表示される。
ここで、GUI上部のコンソールに以下を入力し、Excecuteするとグラフが表示される。
以下は、CPUの利用時間を1分ごとに出力するクエリ。
```
avg without(cpu) (rate(node_cpu_seconds_total{mode!="idle"}[1m]))
```

## 接続確認
```
$ curl -k https://localhost
$ curl -kv https://localhost
```

## Docker
```
$ docker ps -a                      # コンテナの確認
$ docker exec -it hoge bash         # コンテナへの接続（bashなければsh）
```

## nginx  
```
$ sudo systemctl status nginx        # ステータス
$ sudo systemctl reload nginx        # 設定ファイルのリロード（無切断）
$ sudo nginx -t                      # 設定ファイル確認
$ sudo systemctl restart nginx       # 再起動
$ /usr/sbin/nginx -s reopen          # ログローテート
```

## mysql  
```
$ mysql -u isucon -p
mysql> show databases;
mysql> use hoge_db;
mysql> show tables;
mysql> describe hoge_table;
```

## その他一般
```
echo 'eHh4Cg==' | openssl enc -d -base64
```
