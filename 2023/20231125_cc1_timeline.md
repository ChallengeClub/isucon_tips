# ISUCON13 CC1 時系列作業ログ
> **Info:** CC1 = Challenge Club

## 当日スケジュール
- 9:30 ライブ配信開始
- 9:40-10:00 オープニング / 問題説明
- 10:00-18:00 競技
  - 10:00 ポータルサイトで当日マニュアル/ダッシュボード/CloudFormationファイル公開
  - 17:00 リーダーボード更新停止
  - 18:00 競技終了
- 18:00- 主催者による追試
- 18:00-18:20 振り返り/スポンサー紹介など案内
- 19:30 結果発表

## 競技前
- 9:30 ライブ配信開始
  - Youtube画面にぐるぐるマーク（演出!）
- 9:40-10:00 オープニング / 問題説明 
  - 今年はVTuber向け動画配信システムの最適化！

## 競技開始
```
- T00:01        ポータル接続  
- T00:02-00:04  Discord接続対応(hidetake)  
- T00:04-00:06  初回のCloudFormation起動(hidetake)  
- T00:06-00:10  ポータル機能と当日マニュアル確認 
- T00:10-       CloudFormationがFail、調査開始（他のチームは初回4000点獲得中）
- T00:15-       CloudFormation再実行（変更なし）
- T00:17-       CloudFormation再実行（大阪リージョン）
- T00:19        ポータルでチケット起案
- T00:24-       EIP数の制限<5に気付き。昨日の練習スタックを削除してEIP数削減。
- T00:26-       CloudFormation再実行（変更なし）
- T00:30-       インスタンス起動、EC2にSSH接続
- T00:35-       ~/webapp/pdns発見,envcheker実行,hostname変更
- T00:40-       各インスタンスで~/binにisucontoolsをcloneしssh keepalive設定(hidetake)
- T00:40-       go->rust変更(maleicacid)
- T00:46-49     hostname切り戻し
- T00:49-       初回ベンチマーク実行
- T00:52-       isucon-13-f1でgit config --global,init,remote add設定(maleicacid) 
- T00:59-       クライアントからssh -A でつなぐことでgitのプライベートリポジトリへsshで接続出来る。 
- T01:03-       空commit、git add 用のCUIツールを導入しgit add。
- T01:10-       git push(デフォルトの.gitignoreを使用。概ね全ファイルpushなので大きめ。) 
- T01:12-       $ git reset --soft HEAD^でコミットを戻しstageから削除した後.gitignoreを編集。
- T01:17-       WebApp内容確認。（sql,pdnsなど）改変しそうなもののみ再addしフォースプッシュ（git push -f）
- T01:25-       github actions設定(maleicacid) 
- T01:30-       kiwsさんのプライベートリポジトリをmaleicacidさんへのtransferを試すが難しそう
- T01:37-       新Private Repository作成(maleicacid) コラボレータ招待（->hidetake）github selfhost runner設定(maleicacid) 
- T01:46-       etc/nginx,mysql,systemdをバックアップしてnginxのjsonログ化(hidetake)
- T01:49-       rustのサービス停止の解析(maleicacid) 
- T01:56-       git remote urlを新プライベートリポジトリに更新。urlをhttps接続に更新。
- T02:02-       git reset --hard HEAD^ してgit pull、
- T02:09-       ~/webappのresetでuntrackファイルが消えた。（後で復旧することに。）
- T02:20-       isucon3のAMIスナップショット作成とisucon4作成、isucon1,2にgithub selfhost runner.(なるせじゅんが4万8千)
- T02:30-       アプリ動作調査。多数のサブドメイン確認(hidetake)。
- T02:40-       昼休憩兼インタビュー(by Tomo) DNS攻略についての会話。DNS水責め攻撃宣言について。
- T02:50-       host設定してアプリ動作確認。マニュアルの確認。HLSは対象外。
- T03:02-       nginxのjson設定、mysqlのスロークエリon、DB table調査
- T03:40-       isucon3のBench実施。スロークエリログ確認。
- T04:10-       PowerDNS調査(maleicacid) 
- T04:29-       1) BenchmarkがFailしている 2) slow-logで遅いクエリのソース、を手分けして調査
- T04:50-　　　　チケットからBenchmarkが滞留してコケていると判断。1)RDBのIndex調査 2)imageのgithub登録(maleicacid)
- T05:13-       isucon3のBench実施。
- T05:19-       isucon3のBench正常完了（スコア2792）。isucon1の復旧不調。
- T05:23-       MySQLのLivestream関係の3tableにindex追加処置。
- T05:35-       isucon3のBench正常完了（スコア3500）（初回の4053よりダウン）
- T05:37-       isucon1用のcloudformationを作成。
- T05:55-       isucon1用のcloudformationを適用。住処談義。
- T06:04-       cloudformation失敗。割り切ってフルスタック作り直しに切り替え。まず削除開始。
- T06:11-       スタック再作成。06:13成功。クラウドとLAMP/wordpress談義。
- T06:20-       ポータルで失格通告。DMは来てない。マニュアルを確認。競技中の再構築はOK。  
- T06:25-       午後、isucon_tipsにインスタンス情報をhidetakeがcommitしていたことを発見。
- T06:28-       isucon_tipsをgit resetして巻き戻す作業。（一応） 
```

> サーバからgitに安全に繋ぐ方法として以下が有りそう。
1. 最初パスワード等でログイン。認証キャッシュを使う。（誰のでもよくPATも本パスワードも使えて柔軟。）  
`$ git remote add origin https://github.com/<user>/<repository>.git`
`$ git config --global credential.helper 'cache --timeout=2592000'`
1. PersonalAccessTokenを発行してサーバに設定する。（PAT扱いが難。事前にgitで共有し難い。）
`$ git remote add origin https://<user>:<password>@github.com/<user>/<repository>.git`
1. ssh agentを使ってsshでgithubへ繋ぐ。(下記と思いますが未検証。user指定が固定になるのが難。)    
`$ git remote add origin git@github.com/<user>/<repository>.git`
`$ ssh -A isucon13f1`  
