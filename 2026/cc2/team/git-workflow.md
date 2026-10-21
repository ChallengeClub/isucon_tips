# CC2 Gitワークフロー

状態：チーム確認待ち。

攻略ごとの非公開リポジトリ（`target/`）で使う手順です。公開の `isucon_tips` にある運用資料の編集に、競技用の固定branch運用を適用するものではありません。
基本原則は[PLAYBOOK](PLAYBOOK.md)を参照してください。

以下のGitコマンド例は、ローカルの `target/` リポジトリ内で実行します。branch名・ファイル名・SHAは対象に合わせて指定します。
LLMが操作する際は、作業場所のAGENTS.mdの承認条件に従います。

## 1. branchの役割

- `main`：既知の正常状態（Best Known Good）。確認済みの変更を採用します。
- `dev-hidetake`・`dev-moriai`・`dev-nuno-8`：各人の固定作業branch。継続して使います。
- `try-*`：必要な場合だけ使う実験branch。

共用dev branchは作りません。

## 2. 日常の作業と同期

変更をcommitする前に、現在のbranch・status・diffを確認し、対象ファイルを指定してaddします。

```bash
git branch --show-current
git status --short --branch
git diff
# Go実装を変更した場合の例
git add -- webapp/golang/app.go
git diff --cached
git commit -m "Reduce queries on posts page"
git push origin dev-hidetake
```

main更新の通知を受けたら、未コミット変更を整理してから、自分の作業branchで取り込みます。

```bash
git fetch origin
git merge origin/main
```

早めの同期で差分を確認し、同じファイルを触る場合は担当者と調整します。

## 3. 候補commitの測定

1. 測定する変更をcommit・pushし、`git rev-parse HEAD` で候補commit SHAを確認します。
2. 対象環境・候補commit SHA・作業内容をチームへ宣言します。
3. 利用を調整した対象環境へ、そのSHAを指定してdeployします。
4. ログローテート・benchmark・結果保全を行い、KEEP / REVERTを判断します。

測定中は、同じ対象環境への別のdeploy・変更・benchmarkを重ねません。
branchの最新状態を追いかけず、配備するSHAを固定します。複数台構成では、各サーバーの役割と配備対象を確認します。
DB・設定など、SHAだけでは表せない測定条件も記録します。具体的な配備・測定コマンドは、今後RUNBOOKで定めます。

## 4. mainへの採用と共有

通常はPRを使います。

1. 個人branchからmainへのPRを作ります。採用対象の変更だけを含めます。
2. PRに変更内容と測定結果を記載します。
3. メンバー確認後、通常のmerge commit（Create a merge commit）で取り込みます。
4. Discordへmain更新とPRリンクを通知します。
5. 各メンバーはmainを自分の作業branchへ取り込みます。

固定branchを継続利用するため、squash merge・rebase mergeは使わない方針とします。
測定したSHAとmerge後のSHAは異なる場合があるので、両者を区別します。競合解消や他の変更との統合で測定時の内容が変わった場合は、再確認・再測定してから採用します。

PRには、まず次の内容を残します。

```text
変更内容: commentsのindex追加
測定commit: <実際に測定したSHA>
対象環境・実行時刻: <対象と時刻>
結果: PASS / score 12,300 → 15,800
判断: KEEP
測定ID: <測定を識別するID>
詳細結果: <共有先リンク、または実行者名・ローカル保存先>
```

共有先が未整備なら、PR本文に成否・score・測定条件を記載し、詳細ログは実行者が測定ID付きでローカルの `artifacts/` に保管します。生ログをGitへ登録する必要はありません。

Discordは更新通知、GitHub PRは変更内容・測定結果・採用理由の記録に使います。

```text
main更新: abc1234 → def5678
変更: commentsのindex追加
結果: PASS / score 12,300 → 15,800
PR: <URL>
```

mainへの取り込みと実環境へのdeployは別です。deploy完了は別途共有します。

## 5. 競合した場合

1. 競合箇所を読み、必要に応じて担当者と双方の変更意図を確認します。
2. 意図した内容へ修正し、動作を確認します。
3. 解消したファイルを指定してaddし、差分を確認してcommitします。
4. 現在の作業branchへpushします。

エディタの「現在の変更を受け入れる」などの操作だけで、解消済みとは判断しません。
競合解消後に無条件でmainへpushせず、mainへの採用は前節の手順で行います。

## 6. 終盤・緊急時

チームで合意した場合に限り、PRを省略してmainへ直接取り込むことができます。
候補の確認・測定結果の記録・main更新通知は省略しません。

未コミット変更を整理し、最新mainを取得して、確認済みのcommitをmergeします。
以下の `<確認済みのcommit SHA>` は実際のSHAへ置き換えます。

```bash
git switch main
git fetch origin
git merge --ff-only origin/main
git merge --no-ff <確認済みのcommit SHA>
# 差分と必要な動作確認を行ってからpushする
git push origin main
```

PRがない場合は、採用したSHA・変更内容・測定結果をDiscordに記録します。

## 参考：targetの基本構成例

対象環境に合わせて調整します。

```text
target/
├─ webapp/                  # AMI上のwebappと原則同じ
├─ db/
│  └─ schema.sql
├─ infra/                   # 現在EC2で実際に使われている設定（実環境に合わせる）
│  ├─ nginx/
│  ├─ systemd/
│  ├─ mysql/
│  ├─ memcached/
│  └─ logrotate/
├─ docs/
│  └─ environment.md        # 作業用
└─ .gitignore
```
