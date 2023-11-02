ISUCON本の3章に倣い、nginxのログをjson化してreloadとログローテート実施。

## 先にnginxの状態を確認  
```bash
$ systemctl list-unit-files --type=service | grep nginx
nginx.service                                      enabled         enabled
$ sudo systemctl status nginx
● nginx.service - A high performance web server and a reverse proxy server
     Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)
     Active: active (running) since Tue 2023-09-26 12:47:43 UTC; 17min ago
       Docs: man:nginx(8)
    Process: 386 ExecStartPre=/usr/sbin/nginx -t -q -g daemon on; master_process on; (code=exited, status=0/SUCCESS)
    Process: 522 ExecStart=/usr/sbin/nginx -g daemon on; master_process on; (code=exited, status=0/SUCCESS)
   Main PID: 633 (nginx)
      Tasks: 3 (limit: 4416)
     Memory: 12.7M
        CPU: 75ms
     CGroup: /system.slice/nginx.service
             ├─633 "nginx: master process /usr/sbin/nginx -g daemon on; master_process on;"
             ├─634 "nginx: worker process" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" ""
             └─635 "nginx: worker process" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" ""

Warning: some journal files were not opened due to insufficient permissions.
```

## nginx logファイルの保存場所を確認  
```bash
$ less /etc/nginx/nginx.conf
        ##
        # Logging Settings
        ##

        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;
```

## nginx logファイルの内容を確認  
現在のログと、rotateされた過去ログが存在する
```bash 
$ ls /var/log/nginx/
access.log
access.log.1
access.log.10
    :
$ less /var/log/nginx/access.log
94.102.56.8 - - [26/Sep/2023:00:03:29 +0000] "GET / HTTP/1.1" 404 134 "-" "Googlebot/2.1 (+http://www.google.com/bot.html)"
167.248.133.37 - - [26/Sep/2023:00:19:49 +0000] "GET / HTTP/1.1" 404 134 "-" "Mozilla/5.0 (compatible; CensysInspect/1.1; +https://about.censys.io/)"
205.210.31.129 - - [26/Sep/2023:01:16:37 +0000] "GET / HTTP/1.1" 404 162 "-" "Expanse, a Palo Alto Networks company, searches across the global IPv4 space multiple times per day to identify customers&#39; presences on the Internet. If you would like to be excluded from our scans, please send IP addresses/domains to: scaninfo@paloaltonetworks.com"
167.94.145.55 - - [26/Sep/2023:01:44:09 +0000] "GET / HTTP/1.1" 404 162 "-" "-"
167.94.145.55 - - [26/Sep/2023:01:44:10 +0000] "GET / HTTP/1.1" 404 134 "-" "Mozilla/5.0 (compatible; CensysInspect/1.1; +https://about.censys.io/)"
167.179.119.118 - - [26/Sep/2023:01:56:39 +0000] "POST /api/v1/orders HTTP/1.1" 404 162 "-" "cloudflare"
185.216.140.159 - - [26/Sep/2023:02:41:38 +0000] "GET / HTTP/1.1" 400 264 "-" "-"
162.221.192.26 - - [26/Sep/2023:03:02:38 +0000] "GET / HTTP/1.1" 404 197 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
52.68.167.32 - - [26/Sep/2023:03:23:00 +0000] "GET /fapi/v1/time HTTP/2.0" 404 162 "-" "curl/7.68.0"
94.102.56.8 - - [26/Sep/2023:04:06:48 +0000] "GET / HTTP/1.1" 404 134 "-" "Googlebot/2.1 (+http://www.google.com/bot.html)"
167.179.119.118 - - [26/Sep/2023:04:24:17 +0000] "POST /api/v1/hf/orders HTTP/1.1" 404 162 "-" "cloudflare"
```

## log rotateの設定を確認  
dailyに14日分保存
```bash 
$ cat /etc/logrotate.d/nginx
/var/log/nginx/*.log {
        daily
        missingok
        rotate 14
        compress
        delaycompress
        notifempty
        create 0640 www-data adm
        sharedscripts
        prerotate
                if [ -d /etc/logrotate.d/httpd-prerotate ]; then \
                        run-parts /etc/logrotate.d/httpd-prerotate; \
                fi \
        endscript
        postrotate
                invoke-rc.d nginx rotate >/dev/null 2>&1
        endscript
}
```

## logファイルの出力形式をjsonに変更  

ISUCON本とやや違うがそのまま行く。
```bash 
$ cat /etc/nginx/nginx.conf
    :
http {

  log_format json escape=json '{"time": "$time_iso8601",'
    '"host": "$remote_addr",'
    '"port": "$remote_port",'
    '"method": "$request_method",'
    '"uri": "$request_uri",'
    '"vhost": "$host",'
    '"user": "$remote_user",'
    '"status": "$status",'
    '"protocol": "$server_protocol",'
    '"path": "$request_uri",'
    '"req": "$request",'
    '"size": "$body_bytes_sent",'
    '"reqtime": "$request_time",'
    '"apptime": "$upstream_response_time",'
    '"ua": "$http_user_agent",'
    '"forwardedfor": "$http_x_forwarded_for",'
    '"forwardedproto": "$http_x_forwarded_proto",'
    '"referrer": "$http_referer"}';

 access_log /var/log/nginx/access.log json;
    :
```

参考：[NginxのアクセスログをJSON形式で出力する](https://qiita.com/progrhyme/items/c85d28eb18359f3f50d9)

-----
※2023/11/02(木) 更新
isucon12q1の最終形態は以下です。
```
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
-----

## nginxのconfiguration設定が正しいかテスト
sudo で権限問題は解決。
```bash 
$ sudo nginx -t
nginx: [warn] conflicting server name "*.t.isucon.dev" on 0.0.0.0:443, ignored
nginx: [warn] conflicting server name "*.t.isucon.local" on 0.0.0.0:443, ignored
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

## 設定ファイルをReload、またはnginxを再起動  
reloadは無停止。状況に応じてどちらか。
```bash 
$ sudo systemctl reload nginx
$ sudo systemctl restart nginx
```

## このままだと形式の違うログが混在するので手動でログローテート
```bash 
$ mv /var/log/nginx/access.log /var/log/nginx/access.log.old
$ /usr/sbin/nginx -s reopen
```

## nginx logファイル(JSON)の内容を確認 
```bash 
$ less /var/log/nginx/access.log
{"time": "2023-09-26T13:37:22+00:00","host": "220.146.110.192","port": "54178","method": "GET","uri": "/","vhost": "admin.t.isucon.dev","user": "","status": "304","protocol": "HTTP/2.0","path": "/","req": "GET / HTTP/2.0","size": "0","reqtime": "0.000","apptime": "","ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0","forwardedfor": "","forwardedproto": "","referrer": ""}
220.146.110.192 - - [26/Sep/2023:13:37:22 +0000] "GET / HTTP/2.0" 304 0 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0"
{"time": "2023-09-26T13:37:22+00:00","host": "220.146.110.192","port": "54178","method": "GET","uri": "/api/me","vhost": "admin.t.isucon.dev","user": "","status": "500","protocol": "HTTP/2.0","path": "/api/me","req": "GET /api/me HTTP/2.0","size": "39","reqtime": "0.001","apptime": "0.000","ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0","forwardedfor": "","forwardedproto": "","referrer": "https://admin.t.isucon.dev/"}
220.146.110.192 - - [26/Sep/2023:13:37:22 +0000] "GET /api/me HTTP/2.0" 500 39 "https://admin.t.isucon.dev/" "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0"
{"time": "2023-09-26T13:37:22+00:00","host": "220.146.110.192","port": "54178","method": "GET","uri": "/api/me","vhost": "admin.t.isucon.dev","user": "","status": "500","protocol": "HTTP/2.0","path": "/api/me","req": "GET /api/me HTTP/2.0","size": "39","reqtime": "0.001","apptime": "0.000","ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0","forwardedfor": "","forwardedproto": "","referrer": "https://admin.t.isucon.dev/"}
220.146.110.192 - - [26/Sep/2023:13:37:22 +0000] "GET /api/me HTTP/2.0" 500 39 "https://admin.t.isucon.dev/" "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0"
```
**何か両方混じっとりゃせんかね。(´・ω・)いいんかな。。。**  

ToDo:nginx log設定変更作業一式をスクリプト化する。

