# CC2 Team Playbook

ISUCON 2026 CC2 の競技中の基本方針。

Members:

- hidetake
- moriai
- nuno-8

詳細なGit操作は `../team/git-workflow.md`、
具体的な環境操作は `../RUNBOOK.md` を参照する。

---

## 1. 基本原則

- `main` は常に動作可能な Best Known Good とする。
- 変更は「調査 → 変更 → benchmark → KEEP / REVERT」で判断する。
- 出来るだけ一度に複数の変更観点を混ぜない。
- 壊れた変更は長時間粘らない。戻して次へ進む。
- benchmark結果は score と対象commit idをセットで扱う。
- 本番サーバへの変更・deploy・benchmarkはチームに宣言してから行う。

---

## 2. 初動

開始直後は分業する。

- 環境・プロセス・計装確認
- アプリ/API・仕様確認
- DB/schema・SQL確認

把握できた情報は早めにチャットで共有する。  
初動後は担当を固定せず、ボトルネックに応じて作業を切り替える。

---

## 3. 作業宣言

作業開始時に短く宣言する。

例:

> hidetake: nginx設定を確認します  
> moriai: `/posts` のN+1を調査します    
> nuno-8: posts/commentsのindex候補を確認します  

特に以下を触る場合は必ず共有する。

- `infra/nginx/`
- `infra/mysql/`
- `infra/systemd/`
- DB schema
- 初期化処理
- 複数メンバーが触りそうなアプリコード

同じファイルを同時に編集しないことを優先する。

---

## 4. Benchmark

benchmarkは同時に複数人で同インスタンスで実行しない。
実行前に宣言する。

> benchmark回します。対象: private-isu-1, dev-hidetake / commit-abc1234

記録するもの:
- インスタンス
- branch
- commit SHA
- score
- KEEP / REVERT
- 必要なら主要な計測結果

比較不能なbenchmarkを増やさない。

---

## 5. Mainへの採用

改善が確認できた変更だけ `main` に入れる。

`main` 更新時はチームへ共有する。

> main更新: abc1234 → def5678  
> score: 12,300 → 15,800  
> posts.user_id index追加

各メンバーはmain更新を確認したら、自分の作業branchへ取り込む。

---

## 6. 問題が起きたら

原因調査に時間が掛かりそうなら、まず既知の正常状態へ戻す。

優先順位:

1. `main` の既知正常commitへ戻す
2. サービス起動確認
3. benchmark可能状態を復旧
4. 原因調査

「壊れた環境を直しながら次の改善を続ける」は避ける。

---

## 7. 終盤

終盤は大規模変更を避ける。

優先するもの:

- 既知の低リスク改善
- mainへの取り込み
- 3台構成・設定整合確認
- observability負荷の削減
- 環境試験スクリプトの実行
- 再起動試験
- final benchmark

最後に Best Known Good の commit SHA を全員で確認する。

---

## 8. LLM(CodexやClaudeCode)

LLMも本Playbook・Git Workflow・RUNBOOKに従う。

LLMには、

- 調査
- 改善案
- diffレビュー
- ログ解析
- script / Ansible作成

を積極的に任せる。

ただし以下は人間の判断を挟む。

- deploy
- benchmark
- commit / push / merge
- サービス構成変更
- DB変更
- 大きなリファクタリング

会話ログだけを正式な手順としない。  
再利用する知識はRUNBOOK、script、skill等へ反映する。