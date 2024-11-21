# ISUCON14攻略ToDo

## 【スケジュール】
- [ ] 11/21 もくもく会、環境構築（Ansible/pprof/webappで動くもの。nginx/mysqlはオプション。構築手順は確立不要。）
- [ ] 11/26 素振り会、環境を使ってチームで点数アップ演習（環境は触らない。３人で最低１個加点要素を試す。）
- [ ] 11/28 もくもく会、環境整備（Ansible/pprof/webapp/nginx/mysqlで動くもの。構築手順も確立。）
- [ ] 12/3  素振り会、環境を使ってチームで点数アップ演習（github経由でマージ）
- [ ] 12/5  もくもく会、環境整備（フル動作済み。構築手順整備。出来たらnginx/SQL設定替えなどの加点要素。）
- [ ] 12/7　前日演習戦(模擬演習(3h)、必須加点要素クリア確認(SQL/N+1) )
- [ ] 12/8  本戦当日

## 【参加準備と手配】
- [x] cc1チーム登録（ひでたけ）
- [x] 競技環境確認（ポータルから試験用のCloudFormation実施/試験ssh接続）  
- [ ] メンバ全員の登録（よーこさとう）、Discord参加、githubのssh公開鍵登録
- [ ] AWSクーポン入手
- [ ] Discordグループ作成
- [ ] 攻略用のPrivareリポジトリ用意
- [ ] 各自の攻略環境用意（pprotein可視化環境／CICD環境。ssh秘密鍵登録。github codespaces推奨。）
- [ ] お昼ごはん、おやつ、ドリンク、睡眠

## 【攻略準備】
### 11/21

## ■ISUCON本攻略チェックリスト（Action込みメモ）
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
## ■moさん足跡追跡
- [ISUCON過去問関連の計装に関するメモ書き](https://qiita.com/mo124121/items/d99ca8fb39ed54237e9b)
- [isucon-o11y:OvservabilityRepo](https://github.com/mo124121/isucon-o11y/tree/main)
- [isucon13-try:isucon13を構成管理をものすごい勢いでやるトライアル](https://github.com/mo124121/isucon13-try/tree/main)

## ■ToDo
- [ ] isucon13-tryをcodespacesに持って来て新EC2インスタンスに適用してCICDベンチ実施。（isucon14用鍵ペア作成）
- [ ] isucon-o11y/isucon13-try/ISUCON13のwebappで自分版CICDベンチ環境構築。ansible読み/スニペットisucon-tools反映。
