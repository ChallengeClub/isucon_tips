ともさんがCA局になってサーバ証明書セットを作成してくださったのでisucon12q1のnginxに設定してみた。

ファイル
isucon.crt　サーバ証明書  
isucon.key　サーバ秘密鍵  
isuconCA.crt　ブラウザ用RootCA証明書

```bash
$ scp -i ~/.ssh/AWSSandboxkey.pem /c/dev/data/certs/isucon12q_server/* ubuntu@18.179.10.225:~
$ sudo mv isucon.crt /etc/nginx/tls/
$ sudo mv isucon.key /etc/nginx/tls/
$ ls /etc/nginx/tls
csr.pem      extfile.txt    fullchain.pem.ORIG  isucon.key  key.pem.ORIG
dhparam.pem  fullchain.pem  isucon.crt          key.pem

$ service nginx status
● nginx.service - A high performance web server and a reverse proxy server
     Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)
     Active: active (running) since Wed 2023-09-13 07:31:13 UTC; 5h 16min ago
       Docs: man:nginx(8)
    Process: 375 ExecStartPre=/usr/sbin/nginx -t -q -g daemon on; master_process on; (code=exi>
    Process: 486 ExecStart=/usr/sbin/nginx -g daemon on; master_process on; (code=exited, stat>
   Main PID: 541 (nginx)
      Tasks: 3 (limit: 1091)
     Memory: 5.5M
        CPU: 472ms
     CGroup: /system.slice/nginx.service
             ├─541 "nginx: master process /usr/sbin/nginx -g daemon on; master_process on;"
             ├─542 "nginx: worker process" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" >
             └─543 "nginx: worker process" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" >

Sep 13 07:31:12 ip-172-31-10-204 systemd[1]: Starting A high performance web server and a reve>
Sep 13 07:31:13 ip-172-31-10-204 systemd[1]: Started A high performance web server and a rever>

$ less /etc/nginx/nginx.conf
	<略>
        ##
        # Virtual Host Configs
        ##

        include /etc/nginx/conf.d/*.conf;
        include /etc/nginx/sites-enabled/*;
	<略>
$ grep ssl sites-enabled/*
	<略>
sites-enabled/default:  ssl_dhparam         /etc/nginx/tls/dhparam.pem;
sites-enabled/isuports.conf:  listen 443 ssl http2;
sites-enabled/isuports.conf:  ssl_certificate     /etc/nginx/tls/fullchain.pem;
sites-enabled/isuports.conf:  ssl_certificate_key /etc/nginx/tls/key.pem;
	<略>

$ sudo cp isuports.conf isuports.conf.org
$ sudo vi isuports.conf
$ diff isuports.conf isuports.conf.org
7,8c7,8
<   # ssl_certificate     /etc/nginx/tls/fullchain.pem;
<   ssl_certificate     /etc/nginx/tls/isucon.crt;
---
>   ssl_certificate     /etc/nginx/tls/fullchain.pem;
>   ssl_certificate_key /etc/nginx/tls/key.pem;
10,11d9
<   # ssl_certificate_key /etc/nginx/tls/key.pem;
<   ssl_certificate_key /etc/nginx/tls/isucon.key;

$ curl localhost:443
<html>
<head><title>400 The plain HTTP request was sent to HTTPS port</title></head>
<body>
<center><h1>400 Bad Request</h1></center>
<center>The plain HTTP request was sent to HTTPS port</center>
<hr><center>nginx/1.18.0 (Ubuntu)</center>
</body>
</html>
