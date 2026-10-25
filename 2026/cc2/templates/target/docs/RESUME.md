# 保留・再開メモ

状態・最終確認日時：未記入。攻略保留と、service停止・rollback・計装解除を区別する。

| 項目 | 最後に確認した実状態 |
|---|---|
| 採用済みmain SHA・測定ID | 未記入 |
| 実機binary hash・build元SHA | 未記入 |
| 実機ソースとの差・build場所 | 未記入 |
| DB migration・設定差分 | 未記入 |
| 保留PR・branch・KEEP/REVERT | 未記入 |
| 復旧元・操作入口 | 未記入 |
| 計装状態・準備ID | 未記入 |
| 容量・回収済みログの所在 | 未記入 |
| 許可SSH alias・対象との対応 | 未記入（実IP・認証値はGit外） |
| 未解決・未検証・次の候補 | 未記入 |

再開時は接続先・実状態をread-only確認し、採用済み条件へ戻すか保留候補を継続するか決める。
mainをcheckoutしてもbinary・DB・設定は戻らない。再起動後の一時設定は有効と仮定しない。
旧workspaceのaliasを新対象へ向けた場合、そのまま旧workspaceから操作しない。
生ログ・一時ファイル・Gitにない生成物がcloneで復元されるとは考えない。
