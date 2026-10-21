# private-isu操作の参考例

状態：チーム確認待ち。

private-isuで実証した初回benchmark、指定SHAのdeploy・snapshot復元、nginx JSONログ・OS指標・MySQL slow logの手動計測です。例外的なbackend言語（Ruby）の構成に依存します。Goのビルド・実行ファイル配備には対応していません。

## 利用方法

1. [RUNBOOK](RUNBOOK.md)で対象構成と検証範囲を確認します。他問題へそのまま適用しません。
2. `scripts/`・`ansible/`・`infra/`を非公開target直下へコピーし、RUNBOOKを`docs/RUNBOOK.md`へ取り込みます。既存ファイルは差分を確認します。ローカル試験には`tests/`もコピーします。
3. `scripts/config.sh`、`ansible/settings.json`、`ansible/logging-settings.json`を実環境の調査結果で設定します。計測関連には固定のSSHエイリアス・service名・ログ配置があります。
4. 操作を宣言し、必要な承認を得てから検証します。公開資料のこの場所から直接実行しません。

計測は「準備を一度行う→採取開始→別操作でbenchmark→採取終了・解析→調査終了時に復元」に分けます。運営Web画面からのbenchmarkを想定し、計測scriptはbenchmarkerを起動しません。

元実装はprivate-isuで実機検証済みです。この参考例への設定分離・移植後はローカル模擬検証のみで、実際の運営Web画面やISUCON13では未検証です。実インスタンスのIP・認証情報・生ログ・バックアップは含みません。

```bash
python3 -m unittest discover -s tests -v
```

共有例のローカル試験34件が成功し、シェル・Python・JSON・Ansible playbookの構文を確認しました。
テストは一時ディレクトリと模擬コマンドを使い、実際のSSH接続・benchmark・service操作を行いません。配備は同一内容の置換・復元のみ実証しており、異なる機能変更・依存更新・DB復旧は未検証です。
