# User Snipets (hidetake)

## ユーザ切替  
```
$ sudo su - isucon
```

## インストール  
```
$ sudo apt install dstat
$ sudo apt -y install prometheus prometheus-node-exporter
$ sudo apt -y install jq
```

## 環境調査  
```
$ cat /etc/os-release                   # os確認  
$ cat /etc/passwd | grep -v nologin     # user確認  
$ sudo lsof -P -i | grep -v sshd        # process確認
$ sudo ss -tlp | grep hoge              # process確認
$ service --status-all                  # serviceリスト確認
$ systemctl status hoge                 # service確認
$ file hoge                             # file素性確認
```

## 負荷関係 
```
$ stress -c 1
```

## 接続確認
```
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
```
