# 作業環境のひな形

状態：チーム確認待ち。

新しい対象環境では、workspace（ローカルの作業フォルダ）とtarget（非公開Gitリポジトリ）を準備します。対象サーバーとは区別してください。

## コピーするもの

| 元ファイル | コピー先 | 用途 |
|---|---|---|
| [workspace/README.md](workspace/README.md) | workspace/README.md | 対象と資料の入口 |
| [workspace/AGENTS.md](workspace/AGENTS.md) | workspace/AGENTS.md | LLMへの指示 |
| [target/README.md](target/README.md) | target/README.md | 対象リポジトリの説明 |
| [target/docs/RUNBOOK.md](target/docs/RUNBOOK.md) | target/docs/RUNBOOK.md | 対象別の操作手順 |
| [target/docs/STRATEGY-SEEDS.md](target/docs/STRATEGY-SEEDS.md) | target/docs/STRATEGY-SEEDS.md | 未検証のヒント・別戦略のタネ箱 |
| [target/docs/RESUME.md](target/docs/RESUME.md) | target/docs/RESUME.md | 保留・再開時の実機とmainの差 |
| [target/.gitignore](target/.gitignore) | target/.gitignore | 認証ファイル・ログの除外 |

既存ファイルは上書きせず、差分を確認して取り込みます。使用したひな形のcommit SHAを記録し、自動同期しません。

## 前提と未実装の操作

サーバーのログインユーザーはubuntu、アプリの実行ユーザーはisucon、ソース配置フォルダはwebappを想定します。
webappには複数言語があり、初期のbackend言語はGoと想定します。ただし実際のservice設定で確認してください。

共通のdeploy・rollback・benchmark scriptはまだありません。Goのビルド・実行ファイル配備やbenchmarkerの引数は、対象別に実装・検証が必要です。
private-isuで検証した例外的な実装は[個人参考例](../hidetake/examples/private-isu/README.md)へ分離しています。そのまま別問題へ適用しないでください。

利用者とLLMが再開する際は、[再構築メモ](../hidetake/WORKSPACE-RECOVERY.md)で準備と未検証部分を確認します。これはチーム未承認の補足です。
設定・認証情報・生ログをこの公開ひな形へ書き戻しません。

ISUCON13で得た運用上の学びと素材の選び方は[個人の練習引き継ぎメモ](../hidetake/PRACTICE-TRANSFER.md)を参照。対象固有scriptを共通実装として同梱するものではありません。
