# ISUCON13への移行手順

状態：チーム確認待ち。

利用者が新workspaceとEC2を準備し、新しいセッションで移植・攻略を開始するための手順です。実IP・鍵・非公開リポジトリURLは、この公開文書へ記入しません。

## 引き継ぎ資料と到達点

最初に[再構築メモ](WORKSPACE-RECOVERY.md)と[参考例の操作一覧](examples/private-isu/RUNBOOK.md#スクリプト一覧と操作の流れ)を読みます。共通原則はcc2のteam/PLAYBOOK.md・git-workflow.md・RUNBOOK.md、対象固有の事実・コマンドは新target/docs/RUNBOOK.mdへ残します。

| 引き継ぐもの | 到達点・使い方 |
|---|---|
| private-isuの実証 | 指定SHAの同一内容配備・snapshot復元、JSONログ・OS指標・slow logの採取解析、手動benchmarkと分離した無負荷／負荷採取を確認済み |
| 共有参考例 | 元実装は実機実証済み。公開例への移植後はローカル34件の試験と構文確認済み。Go配備・ISUCON13・運営Web画面は未検証 |
| 計測方式 | 一度計装準備し、採取開始後に別操作でbenchmark、結果確定後にEnterで採取終了。採取成功とbenchmarkのPASSは別記録 |
| MySQL調査 | prepared SQLをdigest集計で十分取得できずslow logを採用。MySQLの設定を変えただけでは既存アプリ接続の閾値が変わらない場合がある |
| ログの扱い | SQLのfingerprintにも値・BLOBが残り得る。生ログ・詳細解析はGit外、共有要約は確認済みのラベルと数値 |
| 接続と承認 | SSHエイリアスを接続情報の管理元とし、Ansibleも同じ名前を使う。状態変更は承認済みの操作入口を使用し、別形式でapprovalを迂回しない |

private-isuのservice名・パス・ログ配置・DB接続・ディスク名・成功判定をISUCON13へそのまま流用しません。旧targetの回収記録・実IP・生ログ・バックアップを新targetへまとめてコピーする必要はありません。

## 1. 空の非公開リポジトリを用意する（利用者）

GitHubでISUCON13攻略用の非公開リポジトリを作成し、SSH clone URLを控えます。公開upstreamと攻略用targetは別にします。

## 2. 新workspaceを作る（利用者）

以下はWSL2/Ubuntuでの操作例です。フォルダ名・URLを実際の値へ置き換え、まだ存在しない作業フォルダで実施します。workspace自体にはgit initしません。

```bash
mkdir -p ~/projects/isucon13-practice
cd ~/projects/isucon13-practice

git clone '<攻略用の非公開リポジトリSSH URL>' target
git clone git@github.com:ChallengeClub/isucon_tips.git isucon_tips
mkdir references artifacts

cp isucon_tips/2026/cc2/templates/workspace/README.md README.md
cp isucon_tips/2026/cc2/templates/workspace/AGENTS.md AGENTS.md
mkdir -p target/docs
cp isucon_tips/2026/cc2/templates/target/README.md target/README.md
cp isucon_tips/2026/cc2/templates/target/docs/RUNBOOK.md target/docs/RUNBOOK.md
cp isucon_tips/2026/cc2/templates/target/.gitignore target/.gitignore

git -C isucon_tips rev-parse HEAD
```

READMEへ対象名・非公開targetのURL・参照したisucon_tipsのSHAを記入します。AGENTS.mdへ許可するrepositoryとSSHエイリアスを明記し、操作入口・approvalを迂回しない指示を再構築メモから反映します。共通ツールは必要になってからcloneします。
この段階でprivate-isuの操作scriptは一括コピーせず、対象調査後に必要な処理だけ移植します。

この文書の更新が未pushなら、新cloneにはまだ含まれません。反映後にcloneするか、旧workspaceの最新版のこの文書・WORKSPACE-RECOVERY.mdをローカル参照として読みます。旧workspaceの未コミット成果が自動で新workspaceへ移るとは考えません。

## 3. EC2を用意する（利用者）

[公式README](https://github.com/isucon/isucon13)の「AWS上での過去問環境の構築方法」を確認します。まず競技者用1台で開始します。

- 公式記載の過去問AMIが現在利用可能か、AWSコンソールで確認する。利用不可なら構築方式を改めて相談する。
- 競技構成の目安はc5.large・gp3 40GiB。利用するスペックを記録する。
- キーペアを指定し、ubuntuでログインできるようにする。
- 通信は公式手順に沿い、SSHのTCP/22、HTTPSのTCP/443、DNSのUDP/53について、実際の接続元に必要な範囲を設定する。
- IP、鍵のローカルパス、インスタンスの識別情報をGit外に控える。

公式READMEによると過去問AMIにはbenchmarkerも含まれます。実際の実行場所・引数・名前解決・TLSの条件は接続後に調べます。以前のisucon-benchmarkがそのまま利用できるとは見なしません。
1台でアプリとbenchmarkerを同居させる場合は負荷が競合するため、操作の検証とscore評価を区別し、測定条件に明記します。

## 4. SSH接続を設定する（利用者）

ローカルの~/.ssh/configで、isucon-targetを新EC2へ向けます。IPと鍵はここで管理します。既存のHostブロックを更新し、同名ブロックを重複させません。

```sshconfig
Host isucon-target
    HostName <新EC2の接続先IP>
    User ubuntu
    IdentityFile <秘密鍵のローカル絶対パス>
    IdentitiesOnly yes
```

接続先を変更した後は旧workspaceでremote操作を行いません。ホスト鍵を信頼できる情報と照合し、鍵チェックを無効化せず、利用者のTerminalで接続を確認します。

```bash
ssh isucon-target 'hostname; whoami; uname -r'
```

benchmarkをSSHで別途操作する必要がある場合だけ、その接続先エイリアスを決め、新AGENTS.mdに許可対象として記入します。古いisucon-benchmarkを推測で流用しません。
将来の複数台練習ではisucon-target1・2・3に固定し、inventoryは同じ名前で管理します。scriptの対象指定・ホスト別成果物・復元対象の確認はその段階で行います。

## 5. ローカルツールとRulesを確認する（利用者・新セッション）

同じWSL環境なら既存ツールを利用します。Bash・Python・SSH・Git・Ansible・alp・pt-query-digestの有無とPATHを確認し、不要な再インストールはしません。
SSHのread-only確認と変更系入口のapprovalは別扱いです。現在のRulesの対象はbash target/scripts/に続くdeploy.sh・rollback.sh・nginx-logging.sh・mysql-slowlog.sh・benchmark.shの5形式です。新セッションでも設定が読み込まれることを確認します。Rulesは全てのremote変更を自動で検出する仕組みとは考えません。

## 6. 新しいセッションで最初に依頼する内容

以下を新workspaceで依頼します。接続先の許可は新AGENTS.mdの記載を優先します。

> このworkspaceでISUCON13攻略を開始します。AGENTS.md、README.md、isucon_tips/2026/cc2/hidetake/WORKSPACE-RECOVERY.mdとISUCON13-START.mdを読んでください。まず許可したSSHエイリアスへのread-only調査で構成とbenchmark実行方法を確認し、計装前の初回benchmark実行案を提示してください。remote変更・benchmarkは承認まで行わないでください。private-isu用scriptはそのまま実行しないでください。

続く順序は「初回benchmark→詳細調査・必要ファイル回収→Goの同一内容deploy／rollback→計測移植・実証→最初の性能改善」です。
最初の到達目標は、初回benchmark成功・Go配備復旧成功・計測成功の3つです。本戦前に複数台で操作を通し、チームで受入れ確認します。
