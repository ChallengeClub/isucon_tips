# ISUCON13から次の練習へ引き継ぐこと

2026-10-25。個人の練習で得た知見。チームの詳細な運用合意や、別年度での実証を意味しない。
対象の実IP・private repository・実機backup・生ログ・保留候補は旧targetの再開メモへ記録し、この公開文書へコピーしない。

## 次でも使う流れ

1. 新workspace・private target・許可SSH alias・承認範囲を確認。変更前に実機ソースと関連設定を回収しcommit/pushして保全する。
2. 計装前benchmarkを早期に1回通す。DNS・TLS・初期化等の前提を先に確かめ、問題固有の引数・counter・scoreの意味を確認する。
3. 既存資産から必要なbuild/deploy/rollback・計測の入口だけ選び、対象パス・言語・権限・成功判定を合わせて通す。
4. 単独変更→採取とbenchmark→対象処理とscoreの比較→KEEP/REVERT。PASSでもエラーが残る場合は明示する。
5. 頭打ち時にタネ箱を見る。処理を速くする以外に、不要な仕事を消す・まとめる・入口で扱う・資源を隔離する案を考える。

## 持ち込める素材／調整が必要な部分

| 素材 | ISUCON13で経験したこと | 新対象で再確認すること |
|---|---|---|
| Go build・binary deploy/rollback | リモートbuild、元binary保存、atomic交換、hash・health確認。ローカルbuildも代替素材として保持 | 言語・toolchain・依存・build元SHA・実機ソースbaseline・service・生成物。異なる候補からの実機rollbackは未実証 |
| 計装・採取・解析 | nginx JSON、SQL slow log、OS4種、準備と採取の分離、回収hash、alp/pt-query-digest、READY後に別操作でbenchmark | DB/接続先service・既存接続の閾値・ログ配置・ディスク・負荷区間・容量。再起動で一時設定が戻る場合がある |
| SQL改善の手順 | EXPLAINと実測の照合、索引の単独検証、N+1の一括化、LIKE照合順序を維持した集合処理 | 初期化後のschema維持・ゼロ件/同点・文字種/照合順序・並行更新・ロック。単体高速化がscore向上とは限らない |

実行scriptは旧ISUCON13の非公開target内の対象別資産で、公開Templateには移植していない。
private-isuやISUCON13のscriptをそのまま実行しない。小さな対象差分の調整を優先し、全面的な共通化は受入れ実績が増えてから判断する。
当日の環境にあるtoolchainでのremote buildを有力な初手とし、local buildは必要時に詰める代替素材として保持する。

## 先に揃えるもの

- Git・SSH・Bash・Python、必要なgh・Ansible・alp・pt-query-digestとPATH。ghは対象private repositoryへのアクセスまで確認する。
- Go cacheやAnsible一時領域が操作元で書けること。GoはGOCACHE/GOMODCACHE、Ansibleはlocal tempとSSH control directoryを明示するとsandbox起因の再試行を減らせる。
- リモートのbuild領域へ入る場合は、所有ユーザーとしてcdする。管理者のcwdがアプリユーザーから読めない場合もある。権限を広げて解決しない。
- 許可済み操作入口と権限設定。制約で止まった場合は原因と限定的な対処を整理し、別形式で承認を迂回しない。

## 競技での速度感

- 素材と実行経験を増やす。使わない代替手段の完成度追求や、初動を遅らせる大きな共通化はしない。
- PRは意図・効果・重要な懸念だけ短くし、詳細を別記録へ。レビュー中PRと次の変更は別branchにする。
- dev branchは利用するが、main統合の担当・詳細レビュー方式は練習で合わせる。未確定の担当制を追加の停止条件にしない。
- 実測・推測を分ける。単発score・全採取区間・負荷区間・counter累積・並列SQL時間を混同しない。
- 中断時は採用mainと実機との差を最初に残す。保留はrollbackや計装解除を自動的に意味しない。

## 次はISUCON14

[ISUCON14の新workspace開始メモ](ISUCON14-START.md)へ進む。問題固有の構成・benchmark・チューニングは初回調査で確認し、ISUCON13のDNS対策を前提にしない。
