# 本日のポイント
- isucon12q1インスタンスが壊れてきたので、isucon12q3を新たに作った
- Elastic IPを関連づけることで、IPアドレスを変わらなくした
- isucon12q3は、nginxログのjson化やprometheusは未設定

# Elastic IPでアイスブレイク
「スケールアップするとIP変わるんですか?」 -> 「動的IPなので…」<br>
「Elastic IPは?」 -> 「あっ！停止中インスタンスに関連付いてた！」
以下、オペレーター=hide_takeさん。

Elastic IPをEC2のインスタンスに関連づけると、固定のIPを使い続けられるので、AWSのGUI操作で、関連づけてみた。<br>
実行中インスタンスにも関連付けられる。IPアドレスが固定となるので、今後楽になりそう。

# 前回の復習
「データベース壊れたけど戻せてベンチマークも動いた！でもログをよく見るとエラーを見つけた」 -> 「エラーを探ろう！」

# APIエラーの探求
## ブラウザでの確認
ブラウザの開発者ツールでHTTPのステータスコードを見る -> 確かにエラーが発生している -> curlで試してみるとどうなる?
## curlでのAPIアクセス
curlでHTTPのAPIにアクセスするには、認証が必要。<br>
そこで、ブラウザでログイン後、ブラウザの開発者ツールのHTTPヘッダからCookieをコピー。<br>
これを`curl -b "Cookie文字列" -k URL文字列` でcurlに渡してAPIアクセスしたところ、アクセスできなかったURLにアクセスできるようになった。
## 壊れているかも
ベンチマークでエラーになっているAPIをCookie付きでアクセスしたが、応答のHTTPボディに入っているjsonがほぼ空。行き詰まり感。<br>
「ここいらで新しいインスタンス作って、比較しますか…？」 -> 「それだ！」<br>
自分もAMIからの作成を体験したかったので、オペレーターになる機会に！<br>
以下、オペレーター=ともさん。

# EC2新インスタンスisucon12q2の作成と放棄
ブラウザでAWSにログインし、[ISUCON過去問AMIのgithub](https://github.com/matsuu/aws-isucon)から、ISUCON12予選のAMIをクリック。<br>
名前はisucon12q2、キーはhide_takeさん設定済みのもので作成。セキュリティは新たに作成。<br>
ステータスが起動中になったが、hide_takeさんのキーだと、sshで入ってアカウントを設定して…といったオペレーションが、ともさんからはできなくなる。<br>
そこで、isucon12q2インスタンスは一旦捨て、ともさんのssh公開鍵をAWSにインポート、これを使った新たなインスタンスを作成することに。

# EC2新新インスタンスisucon12q3
## 作成
インスタンス作成は基本的にisucon12q2と同様。名前はisucon12q3に。セキュリティはisucon12q2で作成したものを使用。<br>
起動し、ユーザーubuntuでsshログインできることを確認。

## 設定 
### タイムゾーンの変更
ログ解析時に不便に思っていたので、これを機に設定。
```
sudo timedatectl set-timezone Asia/Tokyo
```
### sshパスワード認証の無効化
### 各ユーザーの作成
### Elastic IPの関連付け
### hostsの変更
- isucon.devではなくisucon.localを使用 -> .devドメインのHSTSを回避できる -> 自己署名証明書の設定が不要に
- 各ユーザーのPCだけでなく、EC2インスタンス内の/etc/hostsも書き換え -> curlでブラウザ同等にアクセス可能に
### デフォルトシェルの変更
個人ユーザーでログインしたところ、シェルが/bin/shになっていたため、bashへ変更。
```
$ chsh
Password:
Changing the login shell for username
Enter the new value, or press ENTER for the default
    Login Shell [/bin/sh]: /bin/bash
```
## 確認
### ブラウザでのアクセス

# TODO
- nginxログのjson化
- prometheusの設定
- 必要なaptパッケージのinstall
