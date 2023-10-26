# 本日のポイント
- isucon12q1インスタンスが壊れてきたので、isucon12q3を新たに作った
- Elastic IPを関連づけることで、IPアドレスを変わらなくした
- isucon12q3は、nginxログのjson化やprometheusは未設定

# Elastic IPでアイスブレイク
「スケールアップするとIP変わるんですか?」 -> 「動的IPなので…」<br>
「Elastic IPは?」 -> 「あっ！停止中インスタンスに関連付いてた！」<br>
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
そこで、isucon12q2インスタンスは一旦放棄、ともさんのssh公開鍵をAWSにインポート、これを使った新たなインスタンスを作成することに。

# EC2新新インスタンスisucon12q3
## 作成
インスタンス作成は基本的にisucon12q2と同様。
- キーは上記の通りインポートしたともさんキーを設定
- 名前は新たにisucon12q3に設定
- セキュリティはisucon12q2で作成したものを使用
  - ただし、HTTPSと9090(Prometheus用)のポート番号も外部からアクセスできるように、穴あけ設定を追加

EC2インスタンスを起動し、ユーザーubuntuでsshログインできることを確認。
## 設定 
### タイムゾーンの変更
ログ解析時に不便に思っていたので、これを機にタイムゾーンをJSTに設定。
```
$ sudo timedatectl set-timezone Asia/Tokyo
```
### sshパスワード認証の無効化
ユーザーに簡単パスワードを設定してしまうと、sshで簡単に入れてしまうため、sshのパスワード認証を無効化。
```
$ sudo sh -c "echo 'PasswordAuthentication no' > /etc/ssh/sshd_config.d/password.conf"
```
### 各ユーザーの作成
ユーザーの作成と公開鍵の設定は、[isucon_tools](https://github.com/ChallengeClub/isucon_tools)にあるツールを使う。<br>
リポジトリ丸ごとEC2インスタンス内でgit cloneして使うのが簡単。
```
$ mkdir git; cd git
$ git clone https://github.com/ChallengeClub/isucon_tools
 :(中略)
$ ./03_createUsers.sh
```
user_info.txtが無いというエラー発生。これはさすがにgithubに上げていなかった。<br>
ローカルでuser_info.txtの内容をもらい、viでコピペ。<br>
再度03_createUsers.shを実行。ユーザーの作成と公開鍵の設置が自動で行われた。すばらしい！
### Elastic IPの関連付け
Elastic IPをisucon12q1から引き剥がし、isucon12q3に関連づければ、今まで通りのadmin.t.isucon.devなどのホスト名でisucon12q3にアクセスできるのでは?<br>
…というコントローラーからの天才的お告げにより、AWSのWebUIにて上記を実施。<br>
インスタンス実行中にも関連付けの変更ができてしまった。ただしsshdのホストキーは引っ越していないので、ssh接続時にエラーとなるはず。その際は~/.ssh/known_hostsを適当に編集下さい。
### hostsの変更
- isucon.devではなくisucon.localを使用 -> .devドメインのHSTSを回避できる -> 自己署名証明書の設定が不要に
- 各ユーザーのPCだけでなく、EC2インスタンス内の/etc/hostsも書き換え -> curlでブラウザ同等にアクセス可能に

/etc/hostsの書き換え前に、適当に別ファイル名でバックアップ。
```
$ sudo cp -a /etc/hosts /etc/hosts.ORIG
```

各ユーザーのhostsファイル(WindowsだとC:¥Windows¥System32¥drivers¥etc¥hosts)や/etc/hostsを、以下に書き換え。
```
(IPアドレス) admin.t.isucon.dev admin.t.isucon.local isucon.t.isucon.dev isucon.t.isucon.local kayac.t.isucon.dev kayac.t.isucon.local
```
(IPアドレス)の部分は、
- 各ユーザーのPCでは、(外部からアクセスできるグローバルな)Elastic IP
- EC2インスタンス内では、127.0.0.1(=localhost)

これにより、どこからでも、同じホスト名で、サービスにアクセスできる。
### デフォルトシェルの変更
個人ユーザーでログインしたところ、シェルがshになっていたため、bashへ変更。
```
$ chsh
Password:
Changing the login shell for username
Enter the new value, or press ENTER for the default
    Login Shell [/bin/sh]: /bin/bash
```
## 確認
### ブラウザでのアクセス
- 管理者画面を見るには: https://admin.t.isucon.local/ -> ログイン名にadminと入れて(入れなくてもよい?)ログイン -> 一覧が出てくる！
- 利用者画面を見るには: https://isucon.t.isucon.local/ -> ログイン名に0001と入れてログイン -> 一覧が出てくる！

/api/adminと/api/playerのどちらも、ブラウザでもcurlでも確認できるようになったはず。<br>
(たぶん)めでたしめでたし(なおベンチマーク未実行…)

# TODO
- nginxログのjson化
- prometheusの設定
- k6など、必要なaptパッケージのinstall
