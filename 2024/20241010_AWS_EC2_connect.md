# 本日のサマリー
- AWS過去問EC2を作成/起動してブラウザでサービス画面を表示した。
- 各自の公開鍵をgithub経由でEC2に登録してsshで接続した。
- 集まったメンバーの自己紹介をした（ゆーこもじゃなりあわのゆんたんおの）

## EC2起動
- [手順](./20241003_ISUCON13過去問環境.md)に従って過去問AMIからEC2インスタンスを開始（今日はたけ/ゆんたん/おのの３名が各自のAWSコンソールでEC2インスタンスを起動）
- 手順中、EC2にPublic IPV4 Addressが付与されない場合があり、インスタンス再作成し。「ネットワーク設定」を編集して「パブリック IP の自動割り当て」を有効化。
- 手順中、EC2にAttachした公開鍵をやっぱり変更したい場合があったが、インスタンスの再作成しかない様子。

## ブラウザでサービスの画面を表示
- ブラウザアクセスできる様にEC2のSecurityGroupのInboundルールにhttp,httpsを追加。
- コンソールでPublicIPAddressを取得(`18.181.182.129`)
- ブラウザで`https://18.181.182.129`にアクセスすると、Welcome to nginx!ページが表示される。
- 自分のマシンのhostファイルに下記を追記。(Windowsの場合はC:\Windows\System32\drivers\etc。管理者権限がいるのでメモ帳でない方が書き込みやすい。)
```Hosts File:hosts
18.181.182.129 pipe.u.isucon.local
18.181.182.129 test001.u.isucon.local
```
- ブラウザで`https://pipe.u.isucon.local`にアクセスするとIsupipeのページが表示される。
- test001ユーザは未設定なので一旦ここまで。

## 各自の公開鍵を登録
- 各自の公開鍵を[isucon_tools](https://github.com/ChallengeClub/isucon_tools)に登録
- EC2インスタンスに公開鍵を設定
  - 各ユーザでログインする場合
  - isuconユーザでログインする場合
    - authorized_keys

## ssh接続してみる


[VSCodeリモート留意点](../2023/20231010_VSCode_RemoteSSH.md#vscode%E3%81%8C%E3%82%B5%E3%83%BC%E3%83%90%E3%83%AA%E3%82%BD%E3%83%BC%E3%82%B9%E3%82%92%E9%A3%9F%E3%81%84%E6%95%A3%E3%82%89%E3%81%8B%E3%81%99)

## 本戦の様子を話す

