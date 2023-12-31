# 本日のポイント
- isucon12q1インスタンスが壊れてきたので、isucon12q3を新たに作った
- Elastic IPを関連付けることで、IPアドレスを変わらなくした
- isucon12q3は、nginxログのjson化やprometheusは未設定

# Elastic IPでアイスブレイク
「スケールアップするとIP変わるんですか?」 -> 「動的IPなので…」<br>
「Elastic IPは?」 -> 「あっ！停止中インスタンスに関連付いてた！」<br>
以下、オペレーター=hide_takeさん。

Elastic IPをEC2のインスタンスに関連付けると、固定のIPを使い続けられるので、AWSのGUI操作で、関連付けてみた。<br>
実行中インスタンスにも関連付けられる。IPアドレスが固定となるので、今後楽になりそう。

# 前回の復習
「データベース壊れたけど戻せてベンチマークも動いた！でもログをよく見るとエラーを見つけた」 -> 「エラーを探ろう！」

# APIエラーの探求

## ブラウザでの確認
ブラウザの開発者ツールでHTTPのステータスコードを見る -> 確かにエラーが発生している -> curlで試してみるとどうなる?

## curlでのAPIアクセス
curlでHTTPのAPIにアクセスするには、認証が必要。<br>
そこで、ブラウザでログイン後、ブラウザの開発者ツールのHTTPヘッダからCookieをコピー。<br>
これを、[こちら](https://qiita.com/beckyJPN/items/e85d40459e7e535dae73)を参考に`curl -b "Cookie文字列" -k URL文字列` でcurlに渡してAPIアクセスしたところ、アクセスできなかったURLにアクセスできるようになった。
```
$ curl -b "isuports_session=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiYWRtaW4iXSwiZXhwIjoxNjk4NDA4NzczLCJpc3MiOiJpc3Vwb3J0cyIsInJvbGUiOiJhZG1pbiIsInN1YiI6ImFkbWluIn0.ht_hv8R-Yyze9CHDAf0jgb4t_kPHZv529o1dzgQZjawgxRO4-5xdcDgwDQeMZCrD_Yn4FodInSbfoyKxiz8ymXw578f-XEqtr2BMEaIxmqrtm2baf15Zzvf7VfXPHzawy2WuHjlba5BaXcCMqQU5MHGXjEeFdmW_EFE57A8g3Jjb8X3Mi7FWeTdL_dTJTj86n1hwC3E8nEf808TykmmfedPXvaW1b2tp89zJhFuhp6E3mmJ8pfzndWTeYd8H3uNv5QSVGfEmYHfvNInWmpgHXKNlaktJuSYW95moO-5gX4jyrbPZUcHrppkSDVL47hUtjbf0inUDloSn81Rm_gjPdA" -k https://admin.t.isucon.local/api/admin/tenants/billing
{
  "status": true,
  "data": {
    "tenants": [
      {
        "id": "167",
        "name": "hidetake-test",
        "display_name": "武知がテストで追加",
        "billing": 0
      },
      {
        "id": "100",
        "name": "lhl-a-100",
        "display_name": "終末の千葉のーと",
        "billing": 61770
      },
      {
        "id": "99",
        "name": "hyx-ppj-99",
        "display_name": "椅子メロン研究所",
        "billing": 7800
      },
      {
        "id": "98",
        "name": "j-p-98",
        "display_name": "やわらかリキュールプリン",
        "billing": 79920
      },
      {
        "id": "97",
        "name": "g-ram-97",
        "display_name": "スピリチュアルアメリカンチェリーの惨劇",
        "billing": 44680
      },
      {
        "id": "96",
        "name": "vx-bem-96",
        "display_name": "こだわりピザ海岸",
        "billing": 107380
      },
      {
        "id": "95",
        "name": "qvec-lfjf-95",
        "display_name": "酎ハイのオタク",
        "billing": 8680
      },
      {
        "id": "94",
        "name": "jepk-dqj-94",
        "display_name": "横浜共和国",
        "billing": 113170
      },
      {
        "id": "93",
        "name": "cryfl-xe-93",
        "display_name": "清酒こわれました",
        "billing": 82780
      },
      {
        "id": "92",
        "name": "lunv-vbtf-92",
        "display_name": "自動ダッシュ部",
        "billing": 14010
      }
    ]
  }
}
```

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
$ sudo systemctl restart sshd
```

### 各ユーザーの作成
ユーザーの作成と公開鍵の設定は、[isucon_tools](https://github.com/ChallengeClub/isucon_tools)にあるツールを使う。<br>
gitは元から入っていたため、リポジトリ丸ごとEC2インスタンス内でgit cloneして使うのが簡単。
```
$ mkdir git; cd git
$ git clone https://github.com/ChallengeClub/isucon_tools
 :(中略)
$ ./03_createUsers.sh
```
ここでuser_info.txtが無いというエラー発生。これはプライバシー懸念でgithubに上げていなかった。<br>
ローカルでuser_info.txtの内容をもらい、viにコピペ。<br>
再度03_createUsers.shを実行。ユーザーの作成と公開鍵の設置が自動で行われたことを/etc/passwdを見て確認。すばらしい！

serviceコマンドによるsshdの再起動がうまく行っていないようだが、一旦気にしない！<br>
なおエラーはこんな感じ。
```
username1 ALL=(ALL) NOPASSWD:ALL
ユーザー username1 が作成され、sudo権限とパスワード確認の省略が設定されました。
Job for ssh.service failed.
See "systemctl status ssh.service" and "journalctl -xeu ssh.service" for details.
SSH公開鍵が設定されました。
```
sshdを手動でも再起動し(もしかして不要?)、ログインできることを確認。

### Elastic IPの関連付け
Elastic IPをisucon12q1から引き剥がし、isucon12q3に関連付ければ、今まで通りのadmin.t.isucon.devなどのホスト名でisucon12q3にアクセスできるのでは?<br>
…というコントローラーからの天才的お告げにより、AWSのWebUIにて上記を実施。<br>
インスタンス実行中にも関連付けの変更ができてしまった。ただしsshdのホストキーは引っ越していないので、ssh接続時にエラーとなるはず。その際は~/.ssh/known_hostsを適当に編集下さい。

### hostsの変更
- isucon.devではなくisucon.localを使用 -> .devドメインのHSTSを回避できる -> 自己署名証明書の設定が不要に(その代わり、.devではHSTSで出てこなかった、ブラウザで変な証明書だけど無視するボタンを押す)
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
- 管理者(admin)画面を見るには: https://admin.t.isucon.local/ -> ログイン名にadminと入れて(入れなくてもよい?)ログイン -> 一覧が出てくる！
- 利用者(player)画面を見るには: https://isucon.t.isucon.local/ -> ログイン名に0001と入れてログイン -> 一覧が出てくる！

過去に*.t.isucon.localや*.t.isucon.devの証明書を独自に発行したCAの証明書を、ブラウザやOSにインポートした方は、削除しましょう。<br>
isucon12q3のnginxにデフォルトで設定されている自己署名証明書の署名検証に失敗して、ブラウザがエラーとなります。

これで、/api/adminと/api/playerのどちらも、ブラウザでもcurlでも確認できるようになったはず。<br>
(たぶん)めでたしめでたし(なおベンチマーク未実行…)

# TODO
isucon12q3に対する、
- nginxログのjson化
- prometheusの設定
- k6など、必要なaptパッケージのinstall
- アプリケーションのgit clone
