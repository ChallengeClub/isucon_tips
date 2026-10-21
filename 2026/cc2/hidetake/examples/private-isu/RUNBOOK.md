# 対象別RUNBOOK

状態：チーム確認待ち。

この参考例には初回benchmark、backend言語（Ruby）のdeploy／rollback、準備と分離した手動計測を含みます。private-isuで検証した実装を基に、接続先などを設定項目へ分離したものです。設定分離後のひな形自体はローカル検証のみです。
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
配備revisionは未確認として記録します。既存のサーバー計装状態は推定せず、modeは`benchmark-only`です。計装前の初回かどうかは実環境で確認します。
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

## 5. 手動計測の前提

この節はコピー後の非公開targetで使う手順です。操作はローカルからSSHで行い、設定変更・ログローテート・アプリ再起動を伴います。承認を得て実行し、同じ対象で複数の計測や別の変更を重ねません。

| 項目 | この実装の前提 |
|---|---|
| SSH | targetは`isucon-target`、ubuntuでログインし、必要な読み取り・変更だけsudoを使う |
| アプリ | systemdの`isu-ruby`。準備・復元時に再起動してDB接続を更新する |
| nginx | `/etc/nginx/nginx.conf`、`/etc/nginx/isucon-json-log.conf`、`/var/log/nginx/access.log`・`error.log` |
| MySQL | MySQL 8.0。sudoのmysqlクライアントがパスワード指定なしのローカル接続で管理できること。`performance_schema`の接続別閾値確認も使う |
| slow log | 準備前はOFF・出力FILE・min_examined_row_limit=0。設定の不一致は自動で上書きしない |
| ローカル | Bash・Python 3・SSH・alp・pt-query-digest。nginx設定変更にはAnsibleも必要。解析ツールはPATHに置く |
| 対象の計測ツール | vmstat・mpstat・pidstat・iostat。ディスク`nvme0n1`、対象プロセスruby・mysqld・nginx・memcachedは実装固定 |

この固定値が異なる場合、scriptと試験を対象に合わせて変更します。`config.sh`の`TARGET_HOST`には`isucon-target`を記入します。benchmark用設定は練習用CLIを使う場合だけ必要です。
移植元で確認した解析ツールはalp 1.0.22、pt-query-digest 3.2.1です。ツールやパッケージは自動導入しません。

`infra/nginx/nginx.conf`はprivate-isuのJSON設定候補です。現行の全設定・include・ログ指定を確認してから取り込みます。現行設定を無条件に置き換えません。
変更前の`/etc/nginx/nginx.conf`のSHA-256を、読み取り調査で確認して`ansible/logging-settings.json`の`baseline_sha256`へ記入します。未設定では適用・復元とも開始しません。
nginx操作専用の`ansible/logging-inventory.yml`は`isucon-target`・ubuntu固定です。deploy用inventoryと設定は別です。

## 6. 準備・採取・復元

以下のIDは毎回重複しない値へ置き換えます。英数字・ハイフン・アンダースコアを使用します。nginx設定ID、MySQL準備ID、測定ID、復元操作IDを区別し、操作結果を記録します。

### 調査開始時に一度準備

```bash
bash target/scripts/nginx-logging.sh --mode enable --run-id <nginx設定ID>
bash target/scripts/mysql-slowlog.sh --mode prepare --run-id <MySQL準備ID>
```

nginxは元の設定を保存してJSON形式を適用し、構文確認・reload・HTTP確認を行います。
MySQLは元設定を保存し、long_query_time=0・slow log ONにします。アプリ再接続後の閾値とHTTP応答も確認します。準備後は有効状態を維持します。
nginxの退避先は`/home/isucon/nginx-log-backups/<nginx設定ID>/`、MySQL設定は`/home/isucon/mysql-log-backups/<MySQL準備ID>/`です。準備失敗時は操作ログと実状態を確認し、復元の要否を判断します。
実行時設定なのでOSやMySQLの再起動後は状態を再確認します。ログ量・ディスク空きは調査中に確認します。

### 測定ごとに採取

```bash
bash target/scripts/measure.sh --run-id <測定ID> --preparation-id <MySQL準備ID>
```

1. 準備状態を確認し、nginx・MySQLの測定前ログを退避・再オープンしてOS採取を開始します。
2. 採取準備完了の表示後、利用者が別操作でWeb画面からbenchmarkを開始します。private-isuの練習では、別ターミナルから第2節のbenchmark.shを使えます。
3. 待機・初期化・負荷走行・最終確認が終わって結果が確定した後、採取側でEnterを押します。
4. OS採取を停止し、測定ログを退避・回収してalpとpt-query-digestで解析します。

scriptはbenchmarkerを起動せず、benchmarkサーバーにも接続しません。端末で前面実行し、LLMの実行ツールではPTYなど標準入力を維持できるセッションを使います。
測定ごとのログ形式・閾値変更やアプリ再起動は行いません。nginxの再オープンとMySQLの`FLUSH LOCAL SLOW LOGS`を使い、前後の設定・nginx hash・アプリMainPIDが一致することを確認します。
配備SHAが確認済みの場合だけ`--deployed-revision <完全なSHA>`を追加します。自動検証ではなく実行者の申告です。

成果物はGit外の`artifacts/<測定ID>/`です。

| ファイル・ディレクトリ | 内容 |
|---|---|
| metadata.json | 採取成否、準備ID、時刻、設定・PIDの前後比較、解析成否 |
| benchmark-result.json | 別操作のjob ID・成否・score・受付／開始／終了時刻・結果保存先を手動記入する欄。未確認値はnullのままにする |
| metrics/ | 1秒間隔のOS・プロセス指標。対象PIDは開始時に取得 |
| logs/・analysis/ | nginxアクセス・エラーログとalp解析 |
| sql/・sql/analysis/ | slow log、転送サイズ・hashの照合記録、pt-query-digest解析 |

`collected`と終了コード0は採取成功であり、benchmarkのPASSではありません。空ログやヘッダーだけのslow logは解析対象なしとして省略します。
採取区間にはWeb操作前の待機も含みます。受付時刻を負荷開始と見なさず、判明した時刻だけ記録し、全体平均と時系列を併せて読みます。
nginxの退避先は`/var/log/nginx/measurements/<測定ID>/{before,measurement}/`、MySQLは`/var/log/mysql/measurements/<測定ID>/{before,measurement}/slow.log`です。現行MySQLの出力先パスは準備IDのままで、ログを再作成して継続します。バックアップ・ログは自動削除しません。

### 中断・解析失敗

EOF・Ctrl+CではOS採取停止を試み、未完了として記録します。外部benchmarkの終了を判断できないためログの終了境界作成・解析・計装復元は行いません。
外部benchmark、現行・退避ログ、計測プロセスを確認してから続けます。再試行は新しい測定IDを使います。設定やアプリPIDの変化を検出した結果を正常な比較に使いません。
正常回収後の解析失敗なら、保存したログに対し個別の解析scriptを使用できます。

```bash
bash target/scripts/analyze-access.sh --run-id <測定ID>
bash target/scripts/analyze-slowlog.sh --run-id <測定ID>
```

解析済み・失敗済みの出力先も上書きしないため、再解析前に既存成果物を保全し、metadataで失敗箇所を確認します。

### 調査終了時に復元

外部benchmarkと採取の両方が終了したことを確認し、承認後に実行します。測定ごとには復元しません。

```bash
bash target/scripts/mysql-slowlog.sh --mode restore \
  --backup-id <MySQL準備ID> --run-id <MySQL復元操作ID>
bash target/scripts/nginx-logging.sh --mode restore \
  --backup-id <nginx設定ID> --run-id <nginx復元操作ID>
```

MySQL復元はアプリ再接続を伴います。設定・アプリ接続の閾値・nginx構文・HTTP応答・service状態を確認します。
復元時に回収するslow logは最後の測定以降の現行ログです。測定ごとのログを結合したものではありません。

## 7. 実証から引き継ぐ知見と未検証事項

- 元実装では、無負荷採取と別CLIによるbenchmarkを同じ準備状態で実施し、設定・アプリPIDを変えずに採取・解析できました。採取とbenchmarkの成否を別記録にしました。
- 回収ログのサイズ・SHA-256、nginxの行数とalp件数、OS採取終了、最終的な設定復元を確認しました。score差から計装負荷や性能向上は断定していません。
- MySQLのPerformance Schema digest集計では、アプリのprepared SQLを十分取得できませんでした。この例はslow logを使い、digest方式の試作は含めません。
- slow logにはPREPARE・CLOSE・収集用SQLも含まれます。レコード数をアプリSQL実行数と同一視しません。
- pt-query-digestのfingerprintにもSQL値やBLOBが残る場合があります。生ログ・詳細解析はGit外に置き、共有要約には確認済みの固定ラベルと数値だけ使います。
- vmstatの最初の値は起動以来の平均です。PID固定の指標では測定中の再起動に注意し、delay accountingが無効な環境でiodelayを根拠にしません。
- 実際の運営Web画面、ISUCON13、Go配備、実機の通信断・容量不足の故障試験は未検証です。Web自動操作・常駐デーモン・正確な負荷区間の自動切り出し・容量の自動監視は未実装です。
- DB基本操作、アプリ固有の追加計装は未整備です。別問題への移植で必要性を確認します。
