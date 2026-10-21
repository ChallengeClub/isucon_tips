# CC2 Team PLAYBOOK

状態：チーム確認待ち。

メンバー：hidetake、moriai、nuno-8。

Git操作の詳細は[Gitワークフロー案](git-workflow.md)、資料・scriptの配置方針は[ADR 0001](../decisions/0001-workspace-layout.md)を参照してください。
共通の操作順序は[RUNBOOK案](../RUNBOOK.md)を参照してください。対象別の具体的なコマンドは、今後整備します。

## 1. 基本原則

- `main` は既知の正常状態（Best Known Good）を保ちます。
- 変更は「調査 → 変更 → benchmark → KEEP / REVERT」で判断します。
- できるだけ一度に複数の変更観点を混ぜません。
- 問題のある変更に長時間粘らず、戻して次の改善へ進みます。

## 2. 初動

開始直後は、事前に決めた次の3つの分担で調査を進めます。

- 環境・プロセス・計装・benchmark準備
- アプリ・API・仕様の確認
- DB・schema・SQLの確認

初回benchmarkは計装前の初期状態で早期に実行し、動作と最初の課題を確認します。
把握した内容は早めに共有します。初動後は役割を固定せず、ボトルネックに応じて切り替えます。

## 3. 作業宣言

作業開始時に、対象と作業内容を短く共有します。

> hidetake：nginx設定を確認します。

同じファイルや設定を触る場合は、担当を調整します。特にmiddleware設定・DB schema・初期化処理・共通のアプリコードを変更する際は、先に共有します。

## 4. Deploy・benchmark

deploy・benchmarkは、開始前に必ず対象環境・候補commit SHA・作業内容をチームへ宣言します。
deploy・ログローテート・測定・結果保全を一まとまりとして担当します。
この間、同じ対象環境への別のdeploy・変更・benchmarkを重ねません。

記録する内容は、次のとおりです。

- 対象環境・実行時刻
- 配備commit SHAと変更内容
- 成否・score
- 結果・ログの保存先
- KEEP / REVERT

## 5. mainへの採用

候補commitで改善を確認してから、`main` へ採用します。
`main` 更新時は、変更内容・commit SHA・測定結果をチームへ共有します。
各メンバーは、更新された `main` を自分の作業branchへ取り込みます。

## 6. 問題が起きたら

復旧に時間がかかりそうなら、まず既知の正常状態へ戻します。
サービスの動作とbenchmark可能な状態を確認してから、原因調査を行います。

## 7. 終盤

大規模変更を避け、次を優先します。

- 既知の正常commitの最終配備
- サーバー構成・設定の整合確認
- 再起動試験
- final benchmark

最後に、配備したBest Known Goodのcommit SHAと測定結果を全員で確認します。

## 8. LLMの利用

LLMには調査・実装案・diffレビュー・ログ解析・script作成を積極的に任せます。
LLMにも本PLAYBOOKとGitワークフロー、RUNBOOKに従ってもらいます。

deploy・benchmark・commit / push / merge・サービス構成変更・DB変更・大きなリファクタリングは、人間の判断を挟みます。
LLMの操作には、作業場所のAGENTS.mdで定めた承認条件も適用します。

会話ログだけを正式な手順とせず、再利用する知識は文書やscriptへ反映します。
