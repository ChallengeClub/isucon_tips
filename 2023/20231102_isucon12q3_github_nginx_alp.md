# 本日のサマリー
- isucon12q3の登録先リポジトリを訂正。(isucon-botの管理からchallenge-clubのorganization管理のものへremote urlを変更）
- windows pull時にファイル名エラーが出たため、/etc/のgitリポジトリ全登録をやめ、/etc/nginxとmysqlのみを登録。
- isucon12q3のnginxログのjson化
- jq,alp,ab導入 
- 上記のおさらいで判明した細々不具合に対応しscriptやsnipet改訂。

## isucon12q3/webappの登録先リポジトリ訂正

isucon_tools/05_add_webapp_to_github.sh
```bash
#!/bin/sh
git config --global user.email "kiwasa28+isucon@gmail.com"
git config --global user.name "isucon"
git config --global init.defaultBranch main
git config --global credential.helper 'cache --timeout=2592000'

cd ~/webapp
git init
git add *
git status
git commit -m "first commit"

git remote add origin https://github.com/ChallengeClub/isucon12q3.git <----- ここ！(ChallengeClub管理）
git push -u origin main
```

```
$ git remote -v
origin  https://github.com/kiws-isucon-bot/isucon12q3-testbot.git (fetch)
origin  https://github.com/kiws-isucon-bot/isucon12q3-testbot.git (push)
$ git remote set-url origin https://github.com/ChallengeClub/isucon12q3.git　<-----  改訂
$ git remote -v
origin  https://github.com/ChallengeClub/isucon12q3.git (fetch)
origin  https://github.com/ChallengeClub/isucon12q3.git (push)
```

## isucon12q3/webapp/etcのエラー対策

etc中にWindowsの禁止命名ファイルがあったため、windowsでclone時にエラー発生。
```
$ git clone https://github.com/ChallengeClub/isucon12q3.git
Cloning into 'isucon12q3'...
remote: Enumerating objects: 1837, done.
remote: Counting objects: 100% (1837/1837), done.
remote: Compressing objects: 100% (1121/1121), done.
remote: Total 1837 (delta 147), reused 1837 (delta 147), pack-reused 0
Receiving objects: 100% (1837/1837), 1.68 MiB | 12.14 MiB/s, done.
Resolving deltas: 100% (147/147), done.
error: invalid path 'etc/systemd/system/multi-user.target.wants/snap-amazon\x2dssm\x2dagent-6563.mount'
fatal: unable to checkout working tree
warning: Clone succeeded, but checkout failed.
You can inspect what was checked out with 'git status'
and retry with 'git restore --source=HEAD :/'
```
etcすべてをgit管理するのではなく、nginx、mysqlのみ管理するようにして、Windowsにクローン出来るようになりました。 
```
$ cd ~/webapp/etc
$ cp -r /etc/nginx .
$ cp -r /etc/mysql .
```

## isucon12q3のnginxログのjson化
### nginx logファイルの保存場所を確認  
```bash
$ less /etc/nginx/nginx.conf
        ##
        # Logging Settings
        ##

        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;
```

### nginx logファイルの状態を確認  
現在のログと、rotateされた過去ログが存在する
```bash 
$ ls /var/log/nginx/
access.log    access.log.2.gz  access.log.4.gz  access.log.6.gz  error.log    error.log.2.gz  error.log.4.gz  error.log.6.gz
access.log.1  access.log.3.gz  access.log.5.gz  access.log.7.gz  error.log.1  error.log.3.gz  error.log.5.gz  error.log.7.gz
```
### nginx logファイルの出力形式をjsonに変更
```
$ cat /etc/nginx/nginx.conf
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
```
### nginxのconfiguration設定が正しいかテスト
```
$ sudo nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```
### 設定ファイルをReload
```bash 
$ sudo systemctl reload nginx
```
### 手動でログローテート
```bash 
$ mv /var/log/nginx/access.log /var/log/nginx/access.log.old
$ /usr/sbin/nginx -s reopen
```
### ブラウザでアクセスしてログの確認
```
cd /var/log/nginx
$ jq . ./access.log
{
  "time": "02/Nov/2023:23:04:29 +0900",
  "host": "111.239.164.67",
  "forwardedfor": "",
  "req": "GET / HTTP/2.0",
  "status": "200",
  "method": "GET",
  "uri": "/",
  "body_bytes": 479,
  "referer": "",
  "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76",
  "request_time": 0,
  "cache": "",
  "runtime": "",
  "response_time": "",
  "vhost": "admin.t.isucon.local"
}
    :
```
### alpでnginxログのサマリ
```
$ alp json --file access.log
+-------+-----+-----+-----+-----+-----+--------+-------------------------------+-------+-------+-------+-------+-------+-------+-------+--------+------------+------------+------------+------------+
| COUNT | 1XX | 2XX | 3XX | 4XX | 5XX | METHOD |              URI              |  MIN  |  MAX  |  SUM  |  AVG  |  P90  |  P95  |  P99  | STDDEV | MIN(BODY)  | MAX(BODY)  | SUM(BODY)  | AVG(BODY)  |
+-------+-----+-----+-----+-----+-----+--------+-------------------------------+-------+-------+-------+-------+-------+-------+-------+--------+------------+------------+------------+------------+
| 1     | 0   | 1   | 0   | 0   | 0   | GET    | /img/isuports_light.svg       | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000  | 1748.000   | 1748.000   | 1748.000   | 1748.000   |
| 1     | 0   | 0   | 0   | 1   | 0   | GET    | /fapi/v1/order                | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000  | 134.000    | 134.000    | 134.000    | 134.000    |
| 2     | 0   | 2   | 0   | 0   | 0   | GET    | /css/app.83b4c321.css         | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000  | 4868.000   | 4868.000   | 9736.000   | 4868.000   |
| 2     | 0   | 2   | 0   | 0   | 0   | GET    | /js/chunk-vendors.40ff55a3.js | 0.000 | 0.565 | 0.565 | 0.282 | 0.565 | 0.565 | 0.565 | 0.282  | 131543.000 | 131543.000 | 263086.000 | 131543.000 |
| 2     | 0   | 2   | 0   | 0   | 0   | GET    | /js/app.3a4ec98c.js           | 0.000 | 0.560 | 0.560 | 0.280 | 0.560 | 0.560 | 0.560 | 0.280  | 33296.000  | 33296.000  | 66592.000  | 33296.000  |
| 3     | 0   | 3   | 0   | 0   | 0   | GET    | /favicon.ico                  | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000  | 4286.000   | 4286.000   | 12858.000  | 4286.000   |
| 4     | 0   | 4   | 0   | 0   | 0   | GET    | /                             | 0.000 | 0.281 | 0.281 | 0.070 | 0.281 | 0.281 | 0.281 | 0.122  | 479.000    | 479.000    | 1916.000   | 479.000    |
| 6     | 0   | 6   | 0   | 0   | 0   | GET    | /api/me                       | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000  | 173.000    | 173.000    | 1038.000   | 173.000    |
+-------+-----+-----+-----+-----+-----+--------+-------------------------------+-------+-------+-------+-------+-------+-------+-------+--------+------------+------------+------------+------------+
```