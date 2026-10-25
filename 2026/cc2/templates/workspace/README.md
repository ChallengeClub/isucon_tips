# 攻略用ワークスペース

状態：チーム確認待ち。

## 攻略対象

- 対象名：未記入
- チーム：未記入
- target repositoryのURL：未記入
- 使用したひな形のisucon_tips commit SHA：未記入

## 配置と役割

作業場所のルート自体はGitリポジトリにせず、各repositoryを個別に管理する構成例です。各人の使いやすさに合わせて調整できます。

| ディレクトリ | 役割 |
|---|---|
| `target/` | 攻略ごとの非公開repository。アプリ・設定・調整済みの共通script・対象固有の記録 |
| `isucon_tools/` | 複数の攻略で再利用する共通ツール |
| `isucon_tips/` | 公開のチーム運用資料・ひな形 |
| `references/` | 読み取り専用の参照repository |
| `artifacts/` | ローカルの測定結果・ログ。Git管理外 |

個人のwrapper・一時調査・ログ回収・解析scriptは、使いやすいローカルの場所へ配置します。

## 読む資料

- 作業規則：作業場所直下の `AGENTS.md`
- チーム原則：`isucon_tips/2026/cc2/team/PLAYBOOK.md`
- Git手順：`isucon_tips/2026/cc2/team/git-workflow.md`
- 共通の操作順序：`isucon_tips/2026/cc2/RUNBOOK.md`
- 対象別の操作手順：`target/docs/RUNBOOK.md`

これらはコピー先の構成を前提とした参照例です。共通資料を別の場所に置く場合は参照先を直します。
日常操作に必要な手順はtarget/docs/RUNBOOK.mdに記録し、共通資料のcloneがない実行環境でも読めるようにします。
SSH設定・認証情報はGit管理外で管理し、実際の接続先は対象別RUNBOOKへ記録します。

## 利用する共通ツール

必要なツールと使用revision：未記入。利用時に確認し、更新は明示的に行います。

最初にGit・SSH・Bash・Python、必要ならgh・Ansible・alp・pt-query-digestと対象言語のtoolchainを確認します。
ghは認証と対象private repositoryへのアクセスまで確認し、認証値は記録しません。不要な再インストールは行いません。
対象別の状態・成果・ヒントはtarget/docsへ記録し、別年度へ移るときは別workspace・別private targetを使います。
