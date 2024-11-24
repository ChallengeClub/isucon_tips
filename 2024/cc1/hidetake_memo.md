## ■ISUCON本攻略チェックリスト
```
	□１章　基礎
		□ top
		□ ベンチマーク
	□２章　モニタリング
		□ stress -c 1
		□ node_expoter(prometeus)
	□３章　負荷試験
		□  nginxのjsonログ
		□ alp
		□ ab
		□ log rotate
		□ slow queryログ(mysqldumpslow)
		□ mysql接続, EXPLAIN, ADD INDEX
		□ dstat
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
## ■環境や攻略のヒント
- [pprotein でボトルネックを探して ISUCON で優勝する](https://zenn.dev/team_soda/articles/20231206000000)
- [ISUCONチートシートv2022 公開版](https://hackmd.io/@to-hutohu/isucon2022)

## ■IUSCON13解説・攻略に沿った攻略
- [ISUCON13 問題の解説と講評(公式)](https://isucon.net/archives/58001272.html)
- [ISUCON13 関連エントリまとめ(公式)](https://isucon.net/archives/57991509.html)
- [ISUCON13に参加して4位になりました (187,577点)](https://blog.p1ass.com/posts/isucon13/)

## ■IUSCON12予選解説に沿った攻略
- [ISUCON12 予選の解説 (Node.jsでSQLiteのまま10万点行く方法)](https://isucon.net/archives/56842718.html)  
- [ISUCON12 予選問題の解説と講評](https://isucon.net/archives/56850281.html)  
```
	□ visit_historyへのindex追加
	□ visit_historyの不要行の削減(300万→20万行)
```
