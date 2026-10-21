# workspace再構築・復旧の補足

状態：チーム確認待ち。

利用者とLLMが別の対象EC2で作業を再開するときのメモです。個別インスタンスの復旧データではありません。

## 最初に利用者へ確認するもの

- 対象問題とマニュアル、対象サーバーのSSHエイリアスとbenchmarkの開始方法。運営Web画面か、練習用CLIかを区別する。
- 攻略用の非公開リポジトリURL。既存のソース・設定・復旧データがあるか。
- 操作を許可する範囲。配備・DB変更・benchmarkの承認を区別する。

不明なURLや接続先を推測しません。共有のrepoや過去ログにない秘密情報は、利用者がGit外で設定します。

## 再開の順序

1. ローカルに非公開target・チーム資料をcloneし、ひな形は既存ファイルを上書きせず取り込む。
2. workspaceのAGENTS.mdへ許可する接続先を記入する。通常調査はubuntu、アプリのHOMEや権限に依存する調査は `sudo -u isucon -H bash -lc '<command>'` を使う。環境全体や認証ファイルを表示しない。
3. SSHホスト鍵・接続を確認する。IP変更で確認が必要でも鍵チェックを無効化しない。
4. 最小限の接続先・実行条件を確認し、承認後、計装前の初回benchmarkを実行して結果をローカルのartifactsへ残す。
5. 事前の分担でserviceのWorkingDirectory・ExecStart・実行ユーザー、webappの配置、DB・初期化・ログを調査して回収する。初期backend言語はGoと想定するがserviceで確認する。
6. ビルド・配備・復旧方法をtarget/docs/RUNBOOK.mdへ記入する。配備前の実行ファイル・設定・権限と、コードだけで戻せないDB状態を確認する。

Gitリポジトリのsnapshotは実サーバーのバックアップではありません。DB schemaだけでは初期データを復元できず、/initializeが全データを復元するとも限りません。
公開upstreamと一致する教材用定数は、秘密らしい名前だけで変更しないでください。実インスタンス固有の認証ファイルは回収対象外です。

## ローカルのAnsible

既存の導入を先に確認します。試行ではWSL2/Ubuntu、ansible-core 2.21.5、専用Python 3.12.10を使用しました。
Ubuntu標準Pythonが3.10の環境では、既存uvを使ってPython 3.12とAnsibleを分離して導入しました。導入は利用者が実施します。

```bash
uv python install 3.12
uv tool install --python 3.12 'ansible-core==2.21.5'
ansible --version
ansible-playbook --version
```

これは再現用の固定バージョンです。新しい環境では対応Python・サポート状況を確認してから選択します。
Ansibleのrawは読み取りコマンドでもCHANGED表示になる場合があります。表示だけで変更の有無を判断しません。通常モジュールはリモート一時ファイルを使うため、完全な読み取り確認とは区別します。

## 引き継ぐべき制約

- 現在の実行script参考例はprivate-isu専用。Goのビルド・実行ファイル配備は未実装。
- 初回benchmarkの引数・結果JSONは問題依存。他問題で成功判定をそのまま流用しない。
- 検証済みなのは同一内容の配備・ファイル復元。異なる機能変更、依存更新、DB復旧は未検証。
- 配備直前のsnapshotと元の実行環境を保存する。元の配備SHAが不明なら推測しない。
- 中断・失敗時は実行ログとリモート状態を確認してから次を実行する。中断した測定の自動再開と、deploy失敗時の自動rollbackは未実装。
- 生ログ・実行ID・接続先・バックアップ所在は非公開targetとGit外のartifactsへ記録する。公開の本メモは実際の復旧データの代わりにはならない。

## 計測を移植するとき

[private-isu参考例のRUNBOOK](examples/private-isu/RUNBOOK.md)に、準備・手動採取・復元を分ける手順と依存構成を保存しています。運営benchmarkerをローカルへ持つことは前提にしません。実際の運営Web画面では未検証です。
新しい問題では最初に初期状態のbenchmarkを実行し、ログ配置・MySQLの版と接続・service・ディスク名を調査してから移植します。Goのdeploy／rollbackは別途実装・検証します。ローカル解析にはalp・pt-query-digestのPATHも確認します。
参考例は公開資料の配置場所から直接実行せず、非公開targetへ必要なscripts・ansible・infraを取り込み、設定と試験を対象に合わせます。チーム標準への昇格は別対象での受入れ確認後に検討します。
