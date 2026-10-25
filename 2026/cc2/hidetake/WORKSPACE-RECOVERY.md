# workspace再構築・復旧の補足

状態：チーム確認待ち。

2026-10-25追記：private-isuからISUCON13への移植・実機試行を実施済み。次の対象は[ISUCON14開始メモ](ISUCON14-START.md)と[練習引き継ぎ](PRACTICE-TRANSFER.md)を優先する。実機の再開情報は非公開targetのRESUME.mdへ残す。

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
4. 接続先・実行条件を確認し、対象への変更前に実環境の `~/webapp` と `/etc` 以下の関連設定を非公開targetへ退避する。秘密情報を除外して復元用metadataを記録し、承認を得てcommit・pushを完了する。DB等の別途保全が必要かも確認する。初期化・更新を伴うbenchmarkも変更に含め、同一インスタンスの保全後に、承認を得て計装前の初回benchmarkを実行しartifactsへ結果を残す。詳細は共通RUNBOOKの「変更前の環境保全」を参照する。
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

- 公開の実行script参考例はprivate-isu専用。ISUCON13の非公開targetではGoのlocal/remote build・binary配備・計測を実証済みだが、汎用scriptとして公開Templateへ同梱していない。
- 初回benchmarkの引数・結果JSONは問題依存。他問題で成功判定をそのまま流用しない。
- ISUCON13では異なる機能のbinary配備とbenchmarkも実証した。変更候補からの実機rollback・DB索引DROP・計装全体の復元は未実証で、同一内容binaryの復旧成功と区別する。
- 配備直前のsnapshotと元の実行環境を保存する。元の配備SHAが不明なら推測しない。
- 中断・失敗時は実行ログとリモート状態を確認してから次を実行する。中断した測定の自動再開と、deploy失敗時の自動rollbackは未実装。
- 生ログ・実行ID・接続先・バックアップ所在は非公開targetとGit外のartifactsへ記録する。公開の本メモは実際の復旧データの代わりにはならない。

## 計測を移植するとき

[private-isu参考例のRUNBOOK](examples/private-isu/RUNBOOK.md)に、準備・手動採取・復元を分ける手順と依存構成を保存しています。運営benchmarkerをローカルへ持つことは前提にしません。実際の運営Web画面では未検証です。
新しい問題では変更前保全後に初期状態のbenchmarkを実行し、ログ配置・DBの版と接続・service・ディスク名を確認して必要な処理だけ移植します。Goのdeploy／rollbackは既存資産を対象に合わせて再検証します。ローカル解析にはalp・pt-query-digestのPATH、PR操作にはghの認証も確認します。
参考例は公開資料の配置場所から直接実行せず、非公開targetへ必要なscripts・ansible・infraを取り込み、設定と試験を対象に合わせます。チーム標準への昇格は別対象での受入れ確認後に検討します。

## 次の対象へ移る際の合意事項

以下はprivate-isuからISUCON13へ移行した際の記録。ISUCON14では新workspace・新しい許可先・新targetを確認し、具体的な操作をそのまま流用しない。

- ISUCON13は別workspace・別の非公開targetリポジトリで進める。旧workspaceは参照元として残し、SSHエイリアス切り替え後は旧workspaceからremote操作を行わない。
- 最初は1台で初回benchmark、Goの同一内容deploy／rollback、計測の移植を確認する。本戦前に複数台練習を一度行い、対象指定・ホスト別成果物・復元対象を検証する。複数台でも攻略リポジトリは1つのtargetとする。
- 接続IP・鍵は各人のSSH configで管理し、Ansible inventoryには同じSSHエイリアスと役割を記載する。IPはinventoryへ重複記載しない。複数台ではisucon-target1・2・3の対応をチームで固定し、役割変更で番号を付け替えない。
- SSHエイリアスはサーバー間通信やbenchmarkのURLには使えるとは限らない。これらの接続値は別途、非公開targetへ記録する。
- 接続先は準備時・変更時・セッション再開時に確認する。毎操作の詳細な環境再調査は不要だが、deploy後の動作確認と測定前の計装状態確認は維持する。
- 設定準備・配備は、単純になる範囲でAnsibleの冪等な処理へ寄せる。測定開始時に設定を自動修復せず、不一致なら停止する。採取・回収・ローカル解析はscriptで制御する。移植前の一括書き直しは行わない。
- 状態変更用の操作入口がある場合はtarget/scripts/*.shを使用する。approvalを避けるために絶対パス・Python本体・raw SSHへ置き換えない。この指示は新workspaceのAGENTS.mdにも反映する。

具体的な利用者の準備手順と再開時の依頼文は[ISUCON13移行手順](ISUCON13-START.md)を参照する。
