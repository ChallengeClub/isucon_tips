# 2023 ISUCON13攻略

[ISUCON13 開催概要(公式)](https://isucon.net/archives/57566481.html)

## ■イベント記録  
- 9/4 ０次予選（２期）⇒チーム登録１枠確保
- 9/6 素振会、miteruさん参加、isucon12q接続、練習AWS環境IAMログイン
- 9/9 ０次予選（３期）⇒チーム登録３枠確保、Discordチャネル作成、isucon_tips(本リポジトリ）作成
- 9/12 素振会、githubリポジトリ作成、tomoさん乱入、isucon12証明書解析、maleicacidさんIAM作成
- 9/13 isucon12のサーバ証明書を発行（tomo）、サーバに登録（hidetake）
- 9/13 isucon_tools（攻略ツール用リポジトリ）作成
- 9/14 takaさん参加（anchobi-naさん含めあと～３人）
- 9/16 10:00～　素振会、github(Project,issue)お試し、共有one note作成
- 9/19 20:00～　takaさん参加、isucon12qベンチマーク実施
- 9/21 21:00～　kiws,miteru,hidetake ToDoの洗い出し prometeus,prometeus-node-expoterをapt install, スケールアップしてstress -c 1とbenchを実施。
- 9/26 21:00～ takaさんSSH設定＠isucon12q1。AWSのIAM発行。nginxログをjson化しログローテート実施。
- 9/28 21:30～ nginxログjson化の修正、alpのインストールと実行、abのインストールと実行。jq導入。
- 10/3 21:00～ ISUCON参加条件クリア（AWS環境チェック）
- 10/5 20:30～ ISUCON参加条件クリア（AWS環境チェック）@miteru, mysql slowlog, add index tenant_id_competition_id_idx(tenant_id, competition_id), bench,
- 10/10 k6を導入しapi呼び出し
- 10/12 振り返り演習（@hidetakeは試作室）
- 10/17 isucon12アプリ構成を確認。Docker等確認。
- 10/19 webappをgithub登録
- 10/24 isucon12予選解説を辿ってvisit_historyにcreated_at含むCovering Index追加。スコア3000→3500とアップ。さっらに解説に従いvisit_historyを300万行→20万行に削減するがベンチに失敗。テーブルを元に戻した。
- 10/26 isucon12q1が壊れ気味のため、isucon12q3を新規に作成。adminに加えplayerでも一覧が取れるようになった。Elastic IPを関連付けてIPアドレスを固定にした。
- 10/31 isucon12q3をシェルスクリプトを書きながら育てようと思ったが、育てるには/etc/の編集が必要。webappとともに/etc/もgithub管理できるよう、本番も想定したgithub運用を検討及び整備。
- 11/02 isucon12q3の登録先リポジトリを訂正。(isucon-botの管理からchallenge-clubのorganization管理のものへ）/etc/の下の全登録をやめ/etc/nginx,mysqlのみに。isucon12q3のnginxログのjson化、jq,alp,ab導入など。
- 11/04 githubのコンフリクトが有ったので練習解消してメモ（hidetake）

## ■ISUCON本攻略チェクリスト
```
	✔１章　基礎
		✔ top
		✔ ベンチマーク
	✔２章　モニタリング
		✔ stress -c 1
		✔ node_expoter(prometeus)
  	✔３章　負荷試験
		✔ nginxのjsonログ
		✔ alp
		✔ ab
  		✔ log rotate
		✔  slow queryログ(mysqldumpslow)
		✔  mysql接続, EXPLAIN, ADD INDEX
		✔ dstat
	□４章　シナリオ試験
		□ k6
	□５章　データベース
    		□ SHOW PLOCESSLIST
     		□ pt-query-digest
     		□ query-digester
      　	□ ADD FULLTEXT INDEX
      　	□ N+1問題
    　　	□ memcached
	□６章　リバースプロキシ
		□ 静的ファイル配信
```
## ■IUSCON12予選解説に沿った攻略
- [ISUCON12 予選の解説 (Node.jsでSQLiteのまま10万点行く方法)](https://isucon.net/archives/56842718.html)  
- [ISUCON12 予選問題の解説と講評](https://isucon.net/archives/56850281.html)  
```
	✔visit_historyへのindex追加
	□ visit_historyの不要行の削減(300万→20万行)
```
## ■ToDo収集
    ✔　全員isuconで作業しなくて良いpermissionを/home/isuconに設定する
    □　nginx log設定変更作業一式をスクリプト化する。
