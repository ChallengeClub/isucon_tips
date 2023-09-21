# User Snipets (hidetake)

## ユーザ切替  
```
$ sudo su - isucon
```

## インストール  
```
$ sudo apt install dstat
$ sudo apt -y install prometheus prometheus-node-exporter
```

## 環境調査  
```
$ cat /etc/os-release                   # os確認  
$ cat /etc/passwd | grep -v nologin     # user確認  
$ sudo lsof -P -i | grep -v sshd        # process確認
$ sudo ss -tlp | grep                   # process確認
$ service --status-all                  # serviceリスト確認
$ systemctl status hogehoge             # service確認
```

## 負荷関係 
```
$ stress -c 1
```

## nginx  
```
```
## mysql  
```
```
