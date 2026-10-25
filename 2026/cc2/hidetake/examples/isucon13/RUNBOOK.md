# 操作入口と検証の流れ

全コマンドは非公開workspace直下で、対象調査・[調整](ADAPTATION.md)と必要な承認後に実行する。
初回変更前の環境保全・commit/pushと、計装前baselineを先に通す。公開例の場所から実行しない。

| 入口（scripts/以下） | 役割と対象への影響 |
|---|---|
| inspect-measurement.sh RUN_ID | 非秘密設定・metadataのread-only確認 |
| build-go-remote.sh COMMIT BUILD_ID ORIGINAL_HASH [LIVE_SOURCE_COMMIT] | 指定commitを別領域でbuild。実機build領域・cacheを変更、serviceは停止しない |
| build-go.sh COMMIT BUILD_ID ORIGINAL_HASH | local buildの代替素材。対象への接続なし |
| deploy.sh BUILD_ID / rollback.sh BUILD_ID | 元binary保存→Go停止→binary交換→起動・health、または保存元へ復旧。DBや配備先ソースは変更しない |
| measurement-tools.sh OP_ID | Ansibleでsysstat導入、常駐採取は有効化しない |
| nginx-logging.sh enable/restore OP_ID PREP_ID | 元設定退避、JSON設定・nginx -t・reload、または復元 |
| mysql-slowlog.sh prepare/restore OP_ID PREP_ID | 元変数保存、slow log閾値0、Go/PowerDNS再接続と疎通確認、または復元 |
| measure.sh RUN_ID MYSQL_PREP_ID | hash・PID・閾値を照合し、ログ境界化・OS採取・回収。設定修復・restart・benchmarkは実行しない |
| analyze-access.sh RUN_ID / analyze-slowlog.sh RUN_ID | 回収成功・hash一致を確認してlocal解析 |
| benchmark.sh RUN_ID | ISUCON13専用の通常benchmarkを1回。別問題では引数と成否判定を確認して組み直す |

## Go配備

build元SHAは40桁・元binary hashは64桁で指定する。remote buildの第4引数を省略すると実機ソースと候補の一致を要求する。
指定すると、そのcommitを実機ソースbaselineとして照合し、機能変更した別commitをbuildできる。
deployが交換するのはbinaryのみで、実機ソースは旧版のまま。再buildはbuild元commit／buildディレクトリから行う。
rollbackは元binaryの復元でありDB migrationやDNS変更を戻さない。失敗時はremoteのstate.jsonとserviceを確認し、無条件に別IDで再実行しない。

## 計測

1. 必要な計装を一度準備する。MySQLの既存接続にも閾値が反映されたことを確認する。
2. measure.shをstdinが維持される前面端末で起動し、READYを待つ。
3. 別操作で承認済みbenchmarkを開始し、実際の結果確定後に採取端末でEnterを押す。
4. 採取成功とbenchmark PASSを別に確認し、採取配下benchmark-result.jsonへ実行ID・結果・保存先を対応付ける。
5. alp・pt-query-digestで解析し、scoreと対象SQL/API・負荷区間のOSを比較する。

EOF/Ctrl+Cは採取未完了として扱う。残留processがないこと、ログ容量、次の測定条件を確認する。
再起動後の一時設定や過去の準備IDを有効と仮定しない。nginx元設定hashが異なる対象へ候補全体を上書きしない。
詳細な実測ID・対象IP・復旧元・生ログは、コピー先の非公開targetとartifactsへ記録する。
