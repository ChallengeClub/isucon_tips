# 目的
HSTSが必須な.devドメインのローカルインスタンスに対して、ブラウザからアクセスできるように、自己署名証明書を発行する。

# 要求
- なるべくISUCON配布イメージの自己署名証明書に近づける
  - CAは*.t.isucon.local
  - サーバー証明書は
    - SANで*.t.isucon.localと*.t.isucon.dev
    - 2048bitのRSA…だったと思う
- なるべく/etc/ssl/以下を変更しない
- 運用は適当
  - 期限は適当
  - CAのシリアルナンバーの管理などは行わない

# 環境
- Ubuntu 22.04
  - OpenSSL 3.0.2

# 手順
## CAの作成
### shellコマンド
```
mkdir -m 700 isuconCA && cd isuconCA

openssl genrsa -out isuconCA.key 2048
openssl req -key isuconCA.key -new -x509 -days 3650 -subj "/CN=*.t.isucon.local" -out isuconCA.crt

cd ..
```

## サーバー証明書の作成とCAの署名
### isucon.conf
```
[req]
default_bits = 2048
distinguished_name = req_distinguished_name
req_extensions = req_ext
prompt = no
[req_distinguished_name]
commonName = *.t.isucon.local
[req_ext]
subjectAltName = @alt_names
[alt_names]
DNS.1 = *.t.isucon.local
DNS.2 = *.t.isucon.dev
```

### san.conf
```
subjectAltName = @alt_names
[alt_names]
DNS.1 = *.t.isucon.local
DNS.2 = *.t.isucon.dev
```

### shellコマンド
```
mkdir -m 700 isucon && cd isucon

openssl genrsa -out isucon.key 2048
openssl req -new -config isucon.conf -key isucon.key -out isucon.csr

openssl x509 -extfile san.conf -req -in isucon.csr -CA ../isuconCA/isuconCA.crt -CAkey ../isuconCA/isuconCA.key -days 3650 -out isucon.crt

cd ..
```

# 感想
- ググった結果がいろいろで、どれをすればよいかわかりづらい
  - 複数の方法がありそう
  - 細かい要求が異なる
  - もっとシンプルにできると思うが、追及はしない
- SANの作成が意外と面倒
  - サーバー証明書の作成とCAの署名段階で`-extfile`による設定が必要と思い至らなかった
    - 証明書の中身を見て、バージョンが3にならないのでSANが入らないということに気づけた
  - ISUCON配布イメージに設定ファイルがあったので、サーバー証明書生成時のCA証明書も入っているのでは説
- ブラウザでのCA証明書のインポートがいろいろ
  - OSで違う
    - ダブルクリックで中間証明書にインポートするOSもある
  - ブラウザで違う
    - FirefoxはOS非依存で独立した証明書セットを持っている?のでわかりやすい
- hostsファイルではなくDNSキャッシュサーバーにIPアドレスを登録したら、正引きに失敗した
  - 解析したらDNNSECの署名検証で失敗していたので、検証対象外ドメインを設定した
    - 私が毒を入れましたの札
    - 自分の環境が毒入れを検知できていることがわかった
