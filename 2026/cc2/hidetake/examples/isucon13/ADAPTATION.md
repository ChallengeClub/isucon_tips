# コピー後に調整する箇所

対象：ISUCON13練習環境を起点にした素材。設定の一元化はしていない。grep等で該当箇所を確認して直接調整する。
192.0.2.10は文書用IPであり、実接続先ではない。

| 対象 | 残している前提／変更箇所 |
|---|---|
| 全入口・inventory | SSH aliasはisucon-target／isucon-benchmark、ubuntu→sudo。新AGENTSの許可先と合わせ、旧環境を指さないことを確認 |
| build_go.py・build_go_remote*.py | webapp/go直下のGoファイル、生成物isupipe、Go 1.21.2、amd64/CGO、Go実体・cache・build領域。Goサブディレクトリを含む構成は対応が必要 |
| go_release*.py | /home/isucon/webapp/go/isupipe、isupipe-go.service、unit・env.shのパス、退避先、GET /api/tagのhealth。候補と実機baselineを区別 |
| slowlog_remote.py | isupipe/isudns両DBの接続を必須確認。GoとPowerDNSをrestart、zone一致とDNS応答IP 192.0.2.10を照合する。ISUCON14へDNS前提を持ち込まない。変更後は対応する模擬試験も更新 |
| metrics_remote.py | process名isupipe/mysqld/nginx/pdns_server、ディスクnvme0n1。対象調査結果へ変更 |
| inspect_measurement_remote.py | 上記service・DB名とnginx siteパス。credentialはmetadataのみという境界を維持 |
| ansible・infra/measurement | 対象inventory、退避先、nginx candidate全体・JSON fragment、health URL。logging-settings.jsonのbaseline_sha256は対象の現行nginx.confのhashへ置換 |
| measurement.py・nginx_log_remote.py・metrics.py | ログ配置・nginx filename・採取するservice/PID・hash。設定準備と採取を分離し、測定時に自動修復しない |
| analyze_access.py | GROUPSはISUCON13の数値IDとAPI。別問題のID形式・ルートに変更。URIや結果へ個人情報が残り得る |
| benchmark.sh | ISUCON13のtarget/nameserver/TLS/domain・CLI引数・JSON成功判定。ISUCON14の決済callback等は新targetで確認して別実装する |

## 移植時に維持する仕組み

- 指定commit由来のbuildと生成物hash。実機binary・ソース・候補metadataが想定外なら停止する。
- 元binaryと所有者・権限等を退避し、失敗時に保存されたphaseを確認してから復旧する。
- 既存DB接続の閾値確認、MySQL再起動後の再確認、secretや環境全体を出力しないこと。
- 採取toolのprocess group全体を停止。READYと終了の境界、途中失敗、回収hashを区別する。
- local artifactはtargetの隣のartifacts/。生ログ・BLOB入りSQL reportをGit登録しない。

## 次の練習での振り返り（未実施）

- 初回benchmark／build-deploy／採取完了までの時刻：
- 素材から修正した箇所と、事前一覧に漏れていた前提：
- そのまま使えた部分、作り直した方が速かった部分：
- sandbox・PATH・認証・権限による再試行：
- 共通化すると得になる箇所／年度別に残す箇所：
