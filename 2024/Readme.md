# 2024 ISUCON14攻略
- [ISUCON14 開催概要(公式)](https://isucon.net/archives/58593190.html)
- [ISUCON公式ブログ](https://isucon.net/)
- [ISUCON公式Github](https://github.com/isucon)
- [ISUCON公式X](https://twitter.com/isucon_official?ref_src=twsrc%5Etfw%7Ctwcamp%5Eembeddedtimeline%7Ctwterm%5Escreen-name%3Aisucon_official%7Ctwcon%5Es1_c1)
- [AWS過去問環境構築Github](https://github.com/matsuu/aws-isucon)

## ■イベント記録  
- 9/24 ０次予選（１期）⇒チーム登録２枠確保(cc1,cc2)、ともたけ
- [9/28](./20240928_%E7%94%B3%E8%BE%BC%E6%88%A6%EF%BC%88%E7%AC%AC%EF%BC%92%E6%9C%9F%EF%BC%89.md) ０次予選（２期）⇒チーム登録２枠追加(cc3,cc4)、あわのいわさ
- [10/1](./20241001_KickOff.md) キックオフ作戦会議（おのいわさともたけ）仲間集めと定例開催の相談（火曜/木曜）
- [10/3](./20241003_ISUCON13過去問環境.md) 初回もくもく回（いわさたけ）。ISUCON13のEC2起動と接続まで
- [10/7](./20241007_ISUCON説明会.md) 社内説明会。ゆーこもじゃなり参加。チーム登録１枠追加(cc5)
- [10/8](./20241008_OnBoarding.md) 素振会。最初のOnBord顔合わせ、初期環境準備
- [10/11](./20241010_AWS_EC2_connect.md) もくもく会。EC2起動して接続
- [10/15](./20241015_ISUCON13攻略.md) 素振会。メンバー開発サービスの紹介。ISUCON13攻略(prometheus導入,ベンチマーク)
- [10/17](./20241017_SUCON13でもくもく会.md) もくもく会。昨年度の本戦当日振り返りをしました。moさんのpprootainはもう少し整備後教えてもらいます。
- [10/22](./2024/20241022_ISUCON13Try.md) 素振り会。チーム編成(outline)。moさんの環境(ansible,pproptain)の解説Q&A。

## ■予定表
- [x] キックオフ作戦会議：10/1(火)21:00～
- [x] 初回もくもく会：10/3(木)21:00～
- [x] 社内説明会：10/7(月)17:30-18:30
    - [x] 社内募集：周囲で強い人とその周囲と参加に興味あるひとに無差別に声をかける。
- [x] 初回素振会：10/8(火)21:00～
    - [x] 参加者自己紹介(抱負/構想)
    - [x] outlineログイン手順、github repoへのcollaborator追加、ssh鍵生成とgithubへの設定、など初期チュートリアル
- [x] もくもく会：10/10(木)21:00～
    - [x] 基本は自由ですが、AWS過去問EC2作成練習(モブプロ) 、ISUCON13インスタンス攻略、攻略リポジトリ構成の相談、など？
- [x] 素振会：10/15(火)21:00～
    - [x] 開発されたサービスの構成紹介が可能でしたら知りたいです :eyes:
    - [x] ISUCON13インスタンス攻略（ベンチマーク、モブプロ）
- [x] もくもく会：10/17(木)21:00～
    - [x] 基本は自由ですが、そろそろ各自のやってみたいことから何か⇒昨年度の本戦当日振り返りをしました。
- [x] 素振会：10/22(火)21:00～
    - [x] 固められるとこからチーム編成を相談
- [ ] もくもく会：10/24(木)21:00～
    - [ ] 基本は自由ですが、組んでモブプロ、ISUCON13インスタンス点数アップ、Ansible/pptotain構成準備など。
- [ ] 10月中くらい 確定メンバーのチーム登録・Discord登録・ssh鍵登録
    - [ ] 「GitHubにSSH鍵が登録されていません」「Discordサーバーに参加していません」のアラートを別途〆切までに対応作業をする。
    - [ ] 招待URLを使って他のメンバー（１チーム計３名まで）を11月7日までに追加する。

## ■ToDo
- [ ] ISUCON13インスタンス攻略（案）
    - [x] ssh接続と環境確認、環境設定
    - [x] ブラウザでサービス画面確認
    - [x] ベンチマーク(bench)実行、結果確認
    - [x] ISUCON本2章モニタリングあたり（prometheus/node-exporter）
    - [ ] ソースコード構成確認、（言語談義・フレームワーク確認）
    - [ ] サービスプロセス確認
- [ ] 高速化 [IUSCON13予選解説](https://isucon.net/archives/58001272.html)に沿った攻略 
- [ ] ISUCON14 SRE Works
    - [x] 負荷測定（prometheus/node-exporter)
    - [x] ログ保存設定（nginx,alp,sql-sloq-logなどのISUCON本3章。)
    - [x] pprotain導入
    - [x] CICD構成 (.gitignore,ansible,docker,ほか)
    - [ ] 負荷分析（newRelic,pprotainなど）
    - [ ] githubcodespacesか攻略用EC2など（各チームで）  
- [ ]　各自の環境整備や操作の確認など
    - [x] github clone/pull/push
    - [x] 情報交換ツール(discode,outline,ほか)
    - [ ] AI支援Tool（gitauto,warp,cursor,ほか）

_誰かが試行済みで聞けば判る状態で✔にしています。_
 
 ## ■ISUCON本攻略チェクリスト
```
	✔ １章　基礎
		✔ top
		✔ ベンチマーク
	□２章　モニタリング
		□ stress -c 1
		✔ node_expoter(prometeus)
	□３章　負荷試験
		□ nginxのjsonログ
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
