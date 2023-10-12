# k6を使ったシナリオ評価

ISUCON本 4章の内容。k6は負荷試験のためのOSS。

## k6のインストール

公式サイトの通りにインストールする。
https://k6.io/docs/get-started/installation/

```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

正しくインストールできているか、バージョンを確認する。
```bash
$ k6 version
k6 v0.47.0 (commit/5ceb210056, go1.21.2, linux/amd64)
```

## k6によるシンプルな負荷試験

教科書通りに、単一URLにリクエストを送信するシナリオを記述。
1⃣並列で30秒間のクエリを送信する。

```js:ab.js
import http from 'k6/http';
const BASE_URL = "http://localhost";

export default function () {
  http.get(`${BASE_URL}/`);
}
```
しかし、アクセスできない。k6ではconnection refusedが発生し、nginxのアクセスログ(/var/log/nginx/access.log)のファイルサイズも増えない。
当然、alpにアクセスログを食わせても、アクセス回数が表示されない。

そこでまず、nginxが動いているか確認する。オプション-nで、ポート番号->名前の変換をせずに表示。
```bash
$ sudo ss -tlp -n | grep nginx
LISTEN 0      511          0.0.0.0:443        0.0.0.0:*    users:(("nginx",pid=655,fd=6),("nginx",pid=654,fd=6),("nginx",pid=643,fd=6))
```

すると、nginxは80番では待ち受けておらず、443番で待ち受けていることがわかった。
これは、httpsのポート番号であり、httpのポート番号ではない。

そこで次に、ab.jsのURLを、httpからhttpsに変更する。

```js:ab.js
import http from 'k6/http';
const BASE_URL = "https://localhost";

export default function () {
  http.get(`${BASE_URL}/`);
}
```

すると、今度はアクセスログのファイルサイズが増えたが、証明書によるエラーが起きているようなので、証明書を無視する。

### 回避策(1)

`--insecure-skip-tls-verify`オプションをつける。

```bash
$ k6 run --vus 1 --duration 30s ab.js --insecure-skip-tls-verify

          /\      |‾‾| /‾‾/   /‾‾/
     /\  /  \     |  |/  /   /  /
    /  \/    \    |     (   /   ‾‾\
   /          \   |  |\  \ |  (‾)  |
  / __________ \  |__| \__\ \_____/ .io

  execution: local
     script: ab.js
     output: -

  scenarios: (100.00%) 1 scenario, 1 max VUs, 1m0s max duration (incl. graceful stop):
           * default: 1 looping VUs for 30s (gracefulStop: 30s)


     data_received..............: 53 MB   1.8 MB/s
     data_sent..................: 7.6 MB  253 kB/s
     http_req_blocked...........: avg=2.06µs   min=181ns   med=240ns    max=12.65ms  p(90)=329ns    p(95)=348ns
     http_req_connecting........: avg=101ns    min=0s      med=0s       max=262.53µs p(90)=0s       p(95)=0s
     http_req_duration..........: avg=106.97µs min=62.26µs med=100.99µs max=19ms     p(90)=118.93µs p(95)=125.19µs
     http_req_failed............: 100.00% ✓ 200677      ✗ 0
     http_req_receiving.........: avg=20.15µs  min=8.1µs   med=18.78µs  max=9.39ms   p(90)=25.95µs  p(95)=31.66µs
     http_req_sending...........: avg=29.55µs  min=12.31µs med=21.25µs  max=9.61ms   p(90)=60.29µs  p(95)=77.89µs
     http_req_tls_handshaking...: avg=1.59µs   min=0s      med=0s       max=12.27ms  p(90)=0s       p(95)=0s
     http_req_waiting...........: avg=57.26µs  min=0s      med=58.76µs  max=10.3ms   p(90)=75.98µs  p(95)=78.23µs
     http_reqs..................: 200677  6689.197015/s
     iteration_duration.........: avg=143.18µs min=82.62µs med=135.49µs max=12.84ms  p(90)=155.69µs p(95)=165.24µs
     iterations.................: 200677  6689.197015/s
     vus........................: 1       min=1         max=1
     vus_max....................: 1       min=1         max=1


running (0m30.0s), 0/1 VUs, 200677 complete and 0 interrupted iterations
default ✓ [======================================] 1 VUs  30s
```

概ね教科書通り実行できた。
abコマンドのRequest per second に相当するものがhttp_reqs、Time per request(mean)に相当するのが http_req_duration のavgとのこと。


```
http_req_duration..........: avg=106.97µs
http_reqs..................: 200677  6689.197015/s
```


### 回避策(2)
こんにちは。Bingです。k6は、Goで開発された負荷試験ツールです1。証明書の無視については、以下の手順を実行することで可能です2:

curlコマンドを使用して、サーバーに接続します。
証明書を無視するために、-kオプションを使用します。
例えば、以下のようになります:

curl -k https://example.com/

また、k6では、証明書の検証を無効にするために、以下の環境変数を設定することもできます3:

export K6_HTTP_INSECURE_SKIP_VERIFY=true

以上の情報がお役に立てることを願っています。

### alpの結果確認
```bash
$ alp json --file access.log
+--------+-----+-----+-----+--------+-----+--------+-----+-------+-------+-------+-------+-------+-------+-------+--------+-----------+-----------+--------------+-----------+
| COUNT  | 1XX | 2XX | 3XX |  4XX   | 5XX | METHOD | URI |  MIN  |  MAX  |  SUM  |  AVG  |  P90  |  P95  |  P99  | STDDEV | MIN(BODY) | MAX(BODY) |  SUM(BODY)   | AVG(BODY) |
+--------+-----+-----+-----+--------+-----+--------+-----+-------+-------+-------+-------+-------+-------+-------+--------+-----------+-----------+--------------+-----------+
| 200677 | 0   | 0   | 0   | 200677 | 0   | GET    | /   | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000  | 162.000   | 162.000   | 32509674.000 | 162.000   |
+--------+-----+-----+-----+--------+-----+--------+-----+-------+-------+-------+-------+-------+-------+-------+--------+-----------+-----------+--------------+-----------+
```

request数 200677と一致する。

# アプリケーションのコード確認

## VSCodeの接続
VSCodeに接続してコードを確認する。別ページ参照.
[20231006_VSCode_RemoteSSH.md](https://github.com/ChallengeClub/isucon_tips/blob/main/2023/20231006_VSCode_RemoteSSH.md)

## isuports.go でコードの確認

Run()内の適当なapiをたたいてみる。
しかし、つながらない。

```bash
$ curl -k https://localhost/api/player/player/:1
<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr><center>nginx/1.18.0 (Ubuntu)</center>
</body>
</html>
```

試しに`https://admin.t.isucon.dev`へアクセスしたところ、アクセスできることが分かったので、こちらへ接続。

```bash
$ curl -k https://admin.t.isucon.dev
<!doctype html><html lang=""><head><meta charset="utf-8"><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="/favicon.ico"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=M+PLUS+1:wght@400;700&display=swap" rel="stylesheet"><title>isuports</title><script defer="defer" src="/js/chunk-vendors.40ff55a3.js"></script><script defer="defer" src="/js/app.3a4ec98c.js"></script><link href="/css/app.83b4c321.css" rel="stylesheet"></head><body><noscript><strong>We're sorry but isuports doesn't work properly without JavaScript enabled. Please enable it to continue.</strong></noscript><div id="app"></div></body></html>
```

別のAPIへ接続してみる。ここでは、api/meへ接続。

```bash
$ curl -k https://admin.t.isucon.dev/api/me
{
  "status": false,
  "message": ""
}
```

結果を見ると、同じcurlによるURLアクセスでも、URLのホスト名がlocalhostの場合と、admin.t.isucon.devの場合では、結果が異なる。
これは、1つのサーバーに対してでも、別の名前でアクセスすると別のコンテンツを返すように(=admin.t.isucon.devでアクセスしないと404が返るように)、nginxが設定されている可能性がある。

# メモ
ベンチマーカーですべて動かすのではなく、k6で指定したAPIだけ評価することも可能。
