# ISUCON13操作の参考例

状態：個人参考例・チーム確認待ち。ISUCON14での移植効率を後で振り返るための素材。

ISUCON13練習で使用したGo build・binary deploy/rollback、nginx JSON・MySQL slow log・OS採取と解析を保存する。
private-isu例と並列の年度別参考例で、共通ツールへ昇格させたものではない。

## 使い始める順序

1. [調整箇所](ADAPTATION.md)と[操作手順](RUNBOOK.md)を読む。
2. 必要なscripts・ansible・infra・testsとexample-review.jsonを、新しい非公開targetのルートへコピーする。既存資産は差分確認して取り込む。
3. 実機をread-only調査してパス・service・toolchain・health・DB依存を調整し、ローカル模擬試験を行う。
4. 調整を確認後、コピー先のexample-review.jsonでreviewed_for_targetをtrueにする。このJSONは実行確認だけで、他の定数を自動設定しない。
5. remote変更・deploy・benchmarkの必要な承認を得て、初回保全・baseline後に必要な入口を通す。

Shell入口は公開例の場所や未確認のコピー先では停止する。Python本体を直接起動してガードを迂回しない。
確認フラグは利用者の実行承認の代わりではない。

## 元実装と公開版の違い

- ISUCON13練習でGo配備・計測を実証したコードから移植した参考例。
- 元の実IPを文書用IP 192.0.2.10へ置換。実機nginxのbaseline hashは未設定値へ置換した。
- 実インスタンスの認証値・private repository URL・生ログ・backup・アプリソース・DB migrationは含めない。
- service名isupipe-go、DB名isupipe/isudns、練習用ドメインu.isucon.local、Go 1.21.2等は年度別の参考値として残す。
- DNS/IP変更や索引追加の攻略scriptは含めない。benchmark.shはISUCON13 CLIの参考で、ISUCON14向けには組み直す。

## 検証範囲

元コードではGo local/remote build、同一内容binaryのdeploy/rollback、機能変更binaryのdeployとbenchmark、計装準備と採取解析を実機で経験した。
機能変更候補からの実機rollback・SQL計装の完全復元は未実証。
公開版への移植後はローカル模擬試験と構文確認を行う。実SSH・service操作・benchmark・ISUCON14での動作は検証していない。

移植後のローカル確認：模擬試験28件成功、Shell・Python・JSONとAnsible playbook 2件の構文確認成功。相対リンクの欠落なし。

```bash
python3 -m unittest discover -s tests -v
```

設定調整を機に大きな抽象化を追加せず、ISUCON14で実際に動かした後に、立上げ時間・修正箇所・失敗・再利用できた部分をADAPTATION.mdの振り返りへ残す。
