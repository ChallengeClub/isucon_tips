# 対象別RUNBOOK

状態：チーム確認待ち。

この参考例には初回benchmarkと、backend言語（Ruby）のソース・静的ファイルのdeploy／rollbackを含みます。private-isuで検証した実装を基に、接続先などを設定項目へ分離したものです。設定分離後のひな形自体はローカル検証のみです。
他言語・依存更新・DB復旧には未対応です。未設定のままリモート操作は開始できません。

この例はprivate-isu専用です。利用先repository内の運用規則と承認条件に従ってください。
作業宣言と必要な承認を得てから実行します。LLMはworkspaceのAGENTS.mdにも従います。

## 1. 準備

- ローカルにBash・Python 3・SSHを用意します。deploy／rollbackにはAnsibleも必要です。
- `scripts/config.sh` にbenchmarkのSSHエイリアス・実行user・binary・userdataの絶対パスを記入します。
- `ansible/settings.json` に対象環境の設定を記入します。

| 設定項目 | 内容 | 例（実環境で確認して変更） |
|---|---|---|
| ssh_alias | 許可された対象サーバーのSSHエイリアス | `isucon-target` |
| login_user | SSHログインユーザー | `ubuntu` |
| app_user / app_group | アプリの所有ユーザー・グループ | `isucon` / `isucon` |
| webapp | ruby/ と public/ を含む既存の配置先の絶対パス | `/home/isucon/private_isu/webapp` |
| backup_root | snapshot・stage・退避ディレクトリを置く絶対パス | `/home/isucon/deploy-backups` |
| app_service | 起動・停止するアプリのsystemd service名 | `isu-ruby` |
| health_url | 対象サーバー内から確認するHTTP URL。初期化など更新処理のないURL | `http://127.0.0.1/` |

設定例ではなく、実際の環境を読み取り確認して記入します。例は公開教材の配置を説明するもので、実インスタンスの接続情報ではありません。認証値は記載しません。
対象固有の設定は非公開targetで管理し、公開のひな形へ戻しません。
service名・初期化方法・DB・ログ配置など、必要な環境情報もこの文書へ追記します。

## 2. 初回benchmark

起動後、計装前の初期状態で動作と最初の課題を確認します。詳細調査・回収完了やログローテートを前提にしません。
以下はコピー後のworkspace直下からの実行形式です。URL・IDは実際の値へ置き換えます。

```bash
BENCHMARK_TARGET_URL='http://<対象の接続先>:80' \
  bash target/scripts/benchmark.sh --run-id <測定ID>
```

scriptはローカルで動き、SSH先で `sudo -n -u <実行user> -H bash -lc` によりbenchmarkerを実行します。
benchmarker固有の初期化・DB更新を伴うことを確認してから実行します。今回のscriptはprivate-isuの引数形式と結果JSONを前提にしているため、別問題では調整が必要です。

結果はworkspaceの `artifacts/<測定ID>/` に保存します。

- metadata.json：対象URL・実行引数・時刻・binary hash・SSH終了コード・成否・score。
- benchmark.stdout.json：benchmarkerのstdout。
- benchmark.stderr.log：SSH・benchmarker等のstderr。

既存IDは上書きしません。SSH終了コード0かつJSONのpass=trueで成功と判定します。
配備revisionは未確認として記録します。候補測定に利用する際の配備SHAとの関連付けは今後整備します。
中断・通信断では再実行前にリモートの実行状態を確認します。

## 3. deploy・rollback

配備対象は、指定commitの `webapp/ruby/` と `webapp/public/` のみです。
設定でwebappの配置先は変えられますが、配備対象ディレクトリを自動で他言語へ切り替える機能はありません。

```bash
bash target/scripts/deploy.sh --revision <commit-SHA> --run-id <配備ID>
bash target/scripts/rollback.sh --backup-id <戻したい配備ID> --run-id <復旧ID>
```

指定SHAをローカルrepositoryからarchive化し、Ansibleで転送します。未コミット変更は含まず、サーバーからGitHubへは接続しません。
Gemfile・Gemfile.lock・prepare_unicorn.rbが現行環境と異なる場合と、ruby配下にvendor・.bundleが存在する場合は、service停止前に拒否します。

現行のruby/publicを `backup_root/<配備ID>/snapshot.tar` に保存後、アプリを停止し、ディレクトリを差し替えて起動します。旧ディレクトリも保持します。
serviceのactiveとhealth_urlのHTTP 200を確認します。benchmarkは自動実行しません。
DB・環境認証ファイル・middleware設定・依存環境は配備対象外です。

rollbackは、指定した配備の「直前の実ファイル」へ戻します。復旧前の状態も別のsnapshotへ保存します。コードだけで復旧できないDB変更などは扱いません。
失敗時の自動rollbackはありません。Ansibleログ・service状態・snapshotの存在を確認して明示的に復旧します。
実行ログとmetadataは `artifacts/<実行ID>/` に保存します。バックアップは自動削除しません。

## 4. 検証済みの範囲と知見

- 元のprivate-isu環境で、初回benchmarkの成功とJSON・metadataの保存を確認しました。
- backend言語のソース・静的ファイル22件を指定SHAから配備し、service active・HTTP 200・内容hashを確認しました。
- snapshot復元後の内容hash・ファイル権限が試行前と一致しました。
- 配備候補は実環境と同一内容でした。異なる機能変更・依存更新・DB復旧は未検証です。
- ローカルHEADと配備SHAは区別します。snapshot復元時に元のrevisionが不明なら推測しません。
- SSHホスト鍵は事前に確認します。接続失敗を理由に確認を無効化しません。
- 操作元Pythonと対象サーバーのPythonは別です。元の試行ではansible-core 2.21.5、操作元Python 3.12.10を使用しました。

生ログ・実環境のID・接続情報は対象の非公開repositoryとGit外のartifactsで管理します。

## 5. 未整備

ログローテート付きbenchmark、DB基本操作、計装・ログ設定変更は今後整備します。
