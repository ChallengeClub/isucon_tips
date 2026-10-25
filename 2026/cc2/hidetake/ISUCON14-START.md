# ISUCON14を新workspaceで始める準備

2026-10-25。ISUCON13攻略保留後の次の練習向け。workspace作成・EC2操作・benchmarkはまだ実施していない。
公式マニュアル・構築方式の確認と新対象の許可は開始時に行う。実URL・IP・鍵・private targetの情報をこの公開メモへ書かない。

## 利用者が用意するもの

- 新しい作業フォルダとISUCON14用private repository。旧targetは再開メモ・素材の参照元として残す。
- 対象EC2と必要なら別benchmarkホスト。構築元cFn/AMIの参照・revision、復旧経路を新targetへ記録する。
- 新AGENTS.mdの許可SSH aliasと操作範囲。可能ならisucon14-target／isucon14-benchmark等の年度を識別できる名前にする。
- 同名aliasを使う場合、付替え後は旧workspaceからremote操作しない。新workspaceの許可欄を埋めるまで接続しない。

## workspaceへ持ち込むもの

workspace自体はGit化せず、targetとisucon_tipsを別repositoryで配置。referencesはread-only、artifactsはGit外。
templates/README.mdのコピー表に沿い、workspaceのAGENTS/README、targetのREADME/RUNBOOK/RESUME/STRATEGY-SEEDS/.gitignoreを取り込む。
ひな形のcommit SHAを記録する。未commit・未pushのTemplate変更は新cloneに含まれないため、反映済みrevisionか旧workspaceのローカル差分を明示して使う。
旧targetの認証情報・生ログ・復旧データや年度固有設定を新targetへ一括コピーしない。

## 最初に通す流れ

1. [練習引き継ぎメモ](PRACTICE-TRANSFER.md)、workspaceの規則、公式問題資料を読む。許可aliasからread-onlyで構成・初期化・benchmark方法を確認。
2. 初動のインフラ担当がprivate repo・invite・構築・ソース設定回収を進め、他の担当がApp/DBを調べる。担当者・並行操作はその練習で確認する。
3. 初回変更前に保全commit/push、承認後に計装前benchmarkを1回。初期化で何が変わるかも記録する。
4. 必要な操作入口だけ旧素材から調整。build/deploy/rollbackと採取を対象に合わせて動かし、初期の改善を単独検証する。
5. 手順の精密化より、確実に通す重要フローと次の攻略へ使える経験を優先する。

## 新セッションへの依頼文

> このworkspaceでISUCON14攻略を開始します。AGENTS.md、README.md、isucon_tips/2026/cc2/hidetake/PRACTICE-TRANSFER.mdとISUCON14-START.mdを読んでください。まず許可したSSHエイリアスへread-only調査を行い、構成・初期化・benchmark実行方法と変更前保全の案を提示してください。remote変更・benchmarkは承認まで行わないでください。旧ISUCON13のtargetは参照元で、scriptをそのまま実行しないでください。操作元ツールとPATH・認証・cache権限も先に確認してください。

新しいprivate repository・接続先・構築方式は未確定。今回のISUCON13に対するcommit/push等の承認を引き継がない。
