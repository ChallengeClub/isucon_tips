# 対象別の操作手順

状態：チーム確認待ち。

この文書を非公開のtargetリポジトリにコピーし、実環境を読み取り確認して記入します。以下の例は架空の設定例であり、そのまま実行する指示ではありません。
ログインユーザーはubuntu、アプリ実行ユーザーはisucon、配置フォルダはwebapp、初期のbackend言語はGoを想定します。実際の起動serviceを優先します。
このひな形に実行scriptは含みません。コマンド欄が未整備の操作は実行しません。

## 1. 準備

ローカルにBash・Python 3・SSHを用意します。Ansibleを利用する配備には、対応する操作元Pythonも必要です。
SSH接続とホスト鍵を事前に確認し、必要な承認を得て操作します。認証値はこの文書へ記載しません。

下表は操作実装に必要な設定項目です。設定ファイルのキーとして利用できますが、読み込むscriptは対象別に整備します。

| 設定項目 | 内容 | 例 |
|---|---|---|
| ssh_alias | 対象サーバーの許可済みSSHエイリアス | `isucon-target` |
| login_user | SSHログインユーザー | `ubuntu` |
| app_user / app_group | アプリ実行ユーザー・所有グループ | `isucon` / `isucon` |
| webapp | backend言語のソースを含む配置先 | `/home/isucon/webapp` |
| backend_language | 稼働するbackend言語 | `go` |
| backend_dir | webapp内のbackend言語ディレクトリ | `golang`（配置を確認） |
| app_service | アプリのsystemd service | `isu-go`（名前を確認） |
| build_command | 指定SHAから実行ファイルを生成する方法 | 未整備：Goバージョン・ビルド場所を確認して決める |
| backup_root | 配備直前のファイルを保存する場所 | `/home/isucon/deploy-backups` |
| health_url | サーバー内から確認する更新処理のないURL | `http://127.0.0.1/` |
| benchmark_ssh_alias | benchmarkを実行するサーバー | `isucon-benchmark` |
| benchmark_command | 対象URL・引数を含む実行方法 | 未整備：対象問題のマニュアルで確認 |
| results_dir | ローカルの実行結果・ログ保存先 | workspaceの `artifacts/<実行ID>/` |

対象名・初期化方法・DB・ログ配置：未記入。
使用したひな形のcommit SHA・必要なツールのバージョン：未記入。

## 2. 初回benchmark

接続先・実行条件・承認を確認し、作業を宣言して計装前の初期状態で実行します。詳細調査・回収・ログローテートの完了を待ちません。
実行コマンド：未整備。終了コードに加え、結果の成否・scoreを確認します。初期化とDB更新の有無は問題ごとに確認します。
対象・実行時刻・実行条件・成否・score・結果の保存先を記録します。ローカルHEADを配備SHAと見なしてはいけません。

## 3. deploy

実行コマンド：未整備。指定commit SHAの内容だけをローカルで取り出し、Ansible等で対象サーバーへ転送する方式を基本とします。
backend言語に必要なビルド・配備ファイル・実行権限を確認します。Goではソースを置き換えるだけで稼働中の実行ファイルが更新されるとは限りません。
復旧元を保存し、アプリを停止して配備・起動・serviceとHTTP応答の確認を行います。依存更新は別途計画します。
認証ファイル・DB・middleware設定はアプリ配備と混ぜません。配備SHA・復旧元ID・結果を記録します。

## 4. rollback

実行コマンド：未整備。配備直前の実ファイルと必要な実行ファイル・権限を復元し、起動とHTTP応答を確認します。
DBや設定変更がある場合、コードだけで復旧できると見なしてはいけません。元の配備SHAが不明なら推測しません。

## 5. 後で整備する操作

ログローテート付きbenchmark、DB基本操作、計装・ログ設定変更は未整備です。
