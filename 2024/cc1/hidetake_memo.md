## ■ISUCON本攻略チェクリスト
```
	✔ １章　基礎
		✔ top
		✔ ベンチマーク
	□２章　モニタリング
		□ stress -c 1（benchが回せれば不要なので参考程度に。）
		✔ node_expoter(prometeus)
	□３章　負荷試験
		✔ nginxのjsonログ(⇒alp向け。pprotein/tsvで問題ない感じ)
		□ alp
		□ ab
  		□ log rotate（⇒ansible化済みなので参考程度に。）
		□ slow queryログ(mysqldumpslow)（⇒ansible化済みなので参考程度に。）
		□ mysql接続, EXPLAIN, ADD INDEX（⇒重要。やろうね！）
		□ dstat（⇒bench中に手元で使えると参考になるよ）
	□４章　シナリオ試験
		□ k6（⇒特定の細かい動作を調べたい時に参考になるはず。やるならcodespacesに入れておくべきと思う。）
	□５章　データベース
    		□ SHOW PLOCESSLIST（⇒pprotein/sqlを補完できるかも）
     		□ pt-query-digest（⇒pprotein/sqlを補完できるかも）
     		□ query-digester（⇒pprotein/sqlを補完できるかも）
      　	□ ADD FULLTEXT INDEX（⇒やろうね。）
      　	□ N+1問題（⇒重要。やろうね！）
    　　	□ memcached
	□６章　リバースプロキシ
		□ 静的ファイル配信（⇒重要。やろうね！）
	□付録
		□ private-isuの攻略実践（⇒各章の対策を順に試せるのでおススメ！な感じ）
		　# unicornプロセス数変更はruby用なのでGoのチームには不要。
		　# alp良い感じ。（json形式でなくtsv形式に出来たらpproteinが使えてその方がベターかも。）
		　# 静的ファイルnginx、画像静的ファイル化は、本番でもそのまま使える技なはず。
		　# pt-query-digest良い感じ。（pprotein/sqlで同じことが出来そうなので代えるのがベターかも。）
		　# joinでN+1を解消、は本番でそのまま使えそうだし効果高そう。超重要！
		　# ファイルディスクリプタ変更も汎用的そう。N+1キャッシュ(memcashed)も実践向きそう。
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
