# ISUCON12q3のベンチに再挑戦
## 本日のサマリー  
* Discordで画面共有するとガビるので、VSCodeのLiveShareを試してみた
* [ISUCON12 予選問題の解説と講評](https://isucon.net/archives/56850281.html)を参考にisucon12q3環境でbench再挑戦してみた

## VSCodeのLiveShareを試してみてわかったこと
Discordで画面共有していると画面がガビガビしてしまうことがあり、共有している内容が把握できないことが多々ありました。そのため、VSCodeのLiveShareを試しています。
色々試してみた結果、VSCodeのLiveShareを使用する際は以下の手順が良さそう。

①[isucon12q3](https://github.com/ChallengeClub/isucon12q3)をローカル環境にgit cloneする
②①でgit cloneしてきたローカルのisucon12q3ディレクトリをVSCodeで開く
③VSCode上のターミナルでAmazon EC2上のisucon12q3環境にSSH接続する
④LiveShare拡張機能を起動して、招待リンクを共有する

※LiveShareの使用方法は、Microsoftの公式ガイド↓を参照ください。
[クイックスタート: Visual Studio Live Share を使用した共同コーディング](https://learn.microsoft.com/ja-jp/visualstudio/liveshare/quickstart/share)

Amazon EC2上で動作しているisucon12q3環境のソースコードをLiveShareしたかったが、実現できませんでした(※)。
そのため、ローカル環境のソースコードをLiveShareしています。
このやり方だと操作内容を共有するときに画面がガビガビする心配がありません。

(※)実現できなかった理由を文章で端的に説明するのは難しいので、気になる方はTakaまでお問い合わせください。

## isucon12q3環境でbench再挑戦したときに試行したこと
本日は、以下順番で試してみました。
* [ISUCON12 予選問題の解説と講評](https://isucon.net/archives/56850281.html)の通りにvisit_historyの不要な行を削除してbench
* updated_at をインデックス追加したテーブルを作成してみる
* updated_atの最小値指定でインデックス追加したテーブルを作成して再度bench (←理解が追い付いていません…)

MySQLの理解が乏しいため、時系列で実施したことをまとめる形になりますがご容赦ください。。
MySQLのコマンドについて調べたことを自分の備忘録として記載しています。

### 予選問題の解説と講評の通りにvisit_historyの不要な行を削除してbench

```bash
isucon@ip-172-31-13-26:~$ mysql -u isucon -p
Enter password:
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 9
Server version: 8.0.35-0ubuntu0.22.04.1 (Ubuntu)

Copyright (c) 2000, 2023, Oracle and/or its affiliates.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| isuports           |
| performance_schema |
+--------------------+
3 rows in set (0.00 sec)

mysql> connect isuports;
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Connection id:    10
Current database: isuports

mysql> CREATE TABLE visit_history_3 AS
    -> SELECT tenant_id, player_id, competition_id, MIN(created_at) AS created_at FROM visit_history GROUP BY tenant_id, player_id, competition_id;
Query OK, 200954 rows affected (26.77 sec)
Records: 200954  Duplicates: 0  Warnings: 0

mysql> show tables;
+--------------------+
| Tables_in_isuports |
+--------------------+
| id_generator       |
| tenant             |
| visit_history      |
| visit_history_2    |
| visit_history_3    |
+--------------------+
5 rows in set (0.00 sec)

mysql> ALTER TABLE visit_history RENAME TO visit_history_old;
Query OK, 0 rows affected (0.01 sec)

mysql> show tables;
+--------------------+
| Tables_in_isuports |
+--------------------+
| id_generator       |
| tenant             |
| visit_history_2    |
| visit_history_3    |
| visit_history_old  |
+--------------------+
5 rows in set (0.00 sec)

mysql> ALTER TABLE visit_history_3 RENAME TO visit_history;
Query OK, 0 rows affected (0.02 sec)

mysql> show tables;
+--------------------+
| Tables_in_isuports |
+--------------------+
| id_generator       |
| tenant             |
| visit_history      |
| visit_history_2    |
| visit_history_old  |
+--------------------+
5 rows in set (0.00 sec)

mysql> CREATE UNIQUE INDEX visit_history_idx ON visit_history(tenant_id, player_id, competition_id);
Query OK, 0 rows affected (2.85 sec)
Records: 0  Duplicates: 0  Warnings: 0

mysql> select count(*) from visit_history;
+----------+
| count(*) |
+----------+
|   200954 |
+----------+
1 row in set (0.02 sec)

mysql> exit;
Bye
```

ログローテートしてからbench実行。
```bash
isucon@ip-172-31-13-26:~$ cd bench/
isucon@ip-172-31-13-26:~/bench$ sudo logrotate -f /etc/logrotate.conf
isucon@ip-172-31-13-26:~/bench$ ./bench -target-addr 127.0.0.1:443
中略
[ADMIN] 13:04:41.209750 GET /api/player/competition/9fa52526/ranking 500 大会内のランキング取得: 入稿と同時
13:04:41.209782 error: 大会内のランキング取得: 入稿と同時 GET /api/player/competition/9fa52526/ranking : expected([200]) != actual(500) tenant:c-oywq-1699535077 role:player playerID:9fa52401 competitionID:9fa52526 rankAfter:
[ADMIN] 13:04:41.209981 allAPISuccessCheck done
[ADMIN] 13:04:41.213920 POST /api/organizer/competition/9fa52405/score 200 大会結果CSV入稿
[ADMIN] 13:04:41.220271 GET /api/player/competition/9fa52405/ranking 500 大会内のランキング取得: ページングなし,上限100件
13:04:41.220332 error: 大会内のランキング取得: ページングなし,上限100件 GET /api/player/competition/9fa52405/ranking : expected([200]) != actual(500) tenant:len-dgqvn-1699535078 role:player playerID:9fa52408 competitionID:9fa52405 rankAfter:
[ADMIN] 13:04:41.220413 rankingCheck failed
[ADMIN] 13:04:41.220460 validation error: error: 大会内のランキング取得: ページングなし,上限100件 GET /api/player/competition/9fa52405/ranking : expected([200]) != actual(500) tenant:len-dgqvn-1699535078 role:player playerID:9fa52408 competitionID:9fa52405 rankAfter:
13:04:41.220466 整合性チェックを終了します
[ADMIN] 13:04:41.220473 Scenario:validation elapsed:3.36990661s
13:04:41.220475 整合性チェックに失敗しました
13:04:42.220656 ERROR[0] prepare: load-validation: GET /api/player/competition/9fa52526/ranking : expected([200]) != actual(500) tenant:c-oywq-1699535077 role:player playerID:9fa52401 competitionID:9fa52526 rankAfter:
13:04:42.220676 ERROR[1] prepare: load-validation: GET /api/player/competition/9fa52405/ranking : expected([200]) != actual(500) tenant:len-dgqvn-1699535078 role:player playerID:9fa52408 competitionID:9fa52405 rankAfter:
[ADMIN] 13:04:42.220862 ScenarioScoreMap: map[string]int64{
  "AdminBilling":            0,
  "AdminBillingValidate":    0,
  "OrganizerNewTenant":      0,
  "OrganizerPeacefulTenant": 0,
  "OrganizerPopularTenant":  0,
  "Player":                  0,
  "PlayerValidate":          0,
  "TenantBillingValidate":   0,
}
[ADMIN] 13:04:42.220948 WorkerCount: map[string]int{}
13:04:42.220986 Error 2 (Critical:0)
13:04:42.220993 PASSED: false
13:04:42.221018 SCORE: 0 (+0 0(2%))
[ADMIN] 13:04:42.221188 score.ScoreTable{
  "GET /api/admin/tenants/billing":                         0,
  "GET /api/organizer/billing":                             0,
  "GET /api/player/competition/:competition_id/ranking":    0,
  "GET /api/player/competitions":                           0,
  "GET /api/player/player/:player_name":                    0,
  "POST /api/admin/tenants/add":                            0,
  "POST /api/organizer/competition/:competition_id/finish": 0,
  "POST /api/organizer/competition/:competition_id/score":  0,
  "POST /api/organizer/competitions/add":                   0,
  "POST /api/organizer/player/:player_name/disqualified":   0,
  "POST /api/organizer/players/add":                        0,
}
```
rankingでエラーになっていそう。
ソースコード上のrankingに関連している関数を検索して、SQL文を直接叩いているコードから怪しそうな箇所を絞り込もうとしたが、複数個所あり時間を要しそうだったので今日は断念。。

### updated_at をインデックス追加したテーブルを作成してみる
```bash
mysql> CREATE TABLE visit_history AS
ayer_id, competition_id, updated_at, MIN(created_a    -> SELECT tenant_id, player_id, competition_id, updated_at, MIN(created_at) AS created_at FROM visit_history_old GROUP BY tenant_id, player_id, competition_id, updated_at;
Query OK, 3210486 rows affected (51.66 sec)
Records: 3210486  Duplicates: 0  Warnings: 0

mysql> show tables;
+--------------------+
| Tables_in_isuports |
+--------------------+
| id_generator       |
| tenant             |
| visit_history      |
| visit_history_old  |
+--------------------+
4 rows in set (0.00 sec)

mysql> select count(*) from visit_history;
+----------+
| count(*) |
+----------+
|  3210486 |
+----------+
1 row in set (0.36 sec)

mysql> show create table visit_history;
+---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Table         | Create Table                                                                                                                                
                                                                                                                                   |
+---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| visit_history | CREATE TABLE `visit_history` (
  `tenant_id` bigint unsigned NOT NULL,
  `player_id` varchar(255) NOT NULL,
  `competition_id` varchar(255) NOT NULL,
  `updated_at` bigint NOT NULL,
  `created_at` bigint
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci |
+---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
1 row in set (0.00 sec)
```
320万行以上のまま変化なし。show create tableで確認したところ、意図通りupdated_atが追加されている。

### updated_atの最小値指定でインデックス追加したテーブルを作成して再度bench
```bash
mysql> CREATE TABLE visit_history AS
    -> SELECT tenant_id, player_id, competition_id, MIN(updated_at) AS updated_at, MIN(created_at) AS created_at FROM visit_history_old GROUP BY tenant_id, player_id, competition_id, updated_at, created_at;
Query OK, 3210486 rows affected, 2 warnings (53.37 sec)
Records: 3210486  Duplicates: 0  Warnings: 2

mysql> select count(*) from visit_history;
+----------+
| count(*) |
+----------+
|  3210486 |
+----------+
1 row in set (0.37 sec)

mysql> show create table visit_history;
+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Table         | Create Table                                                                                                                                
                                                                                                                          |
+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| visit_history | CREATE TABLE `visit_history` (
  `tenant_id` bigint unsigned NOT NULL,
  `player_id` varchar(255) NOT NULL,
  `competition_id` varchar(255) NOT NULL,
  `updated_at` bigint,
  `created_at` bigint
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci |
+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
1 row in set (0.00 sec)

mysql> CREATE UNIQUE INDEX visit_history_idx ON visit_history(tenant_id, player_id, competition_id, updated_at);
Query OK, 0 rows affected (33.40 sec)
Records: 0  Duplicates: 0  Warnings: 0

mysql> select count(*) from visit_history;
+----------+
| count(*) |
+----------+
|  3210486 |
+----------+
1 row in set (0.39 sec)

mysql> show create table visit_history;
+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Table         | Create Table                                                                                                                                
                                                                                                                                                              
                                                      |
+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| visit_history | CREATE TABLE `visit_history` (
  `tenant_id` bigint unsigned NOT NULL,
  `player_id` varchar(255) NOT NULL,
  `competition_id` varchar(255) NOT NULL,
  `updated_at` bigint,
  `created_at` bigint,
  UNIQUE KEY `visit_history_idx` (`tenant_id`,`player_id`,`competition_id`,`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci |
+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
1 row in set (0.00 sec)
```
今回も320万行以上のまま削減されない。。
ログローテートしてから再度bench実行してみる。
```bash
isucon@ip-172-31-13-26:~/bench$ sudo logrotate -f /etc/logrotate.conf
isucon@ip-172-31-13-26:~/bench$ 
isucon@ip-172-31-13-26:~/bench$ ./bench -target-addr 127.0.0.1:443
中略
[ADMIN] 13:54:39.959928 GET /api/player/competition/9fa5252f/ranking 500 大会内のランキング取得: 入稿と同時
13:54:39.959960 error: 大会内のランキング取得: 入稿と同時 GET /api/player/competition/9fa5252f/ranking : expected([200]) != actual(500) tenant:gr-wwxceh-1699538076 role:player playerID:9fa52401 competitionID:9fa5252f rankAfter:
[ADMIN] 13:54:39.960133 allAPISuccessCheck done
[ADMIN] 13:54:39.970102 GET /api/player/competition/9fa52404/ranking 200 大会内のランキング取得: ページングなし,上限100件
[ADMIN] 13:54:39.973806 GET /api/player/competition/9fa52404/ranking 500 大会内のランキング取得: ページングあり
13:54:39.973825 error: 大会内のランキング取得: ページングあり GET /api/player/competition/9fa52404/ranking : expected([200]) != actual(500) tenant:qbbid-ifmst-1699538076 role:player playerID:9fa52407 competitionID:9fa52404 rankAfter:100
[ADMIN] 13:54:39.973872 rankingCheck failed
[ADMIN] 13:54:39.973888 validation error: error: 大会内のランキング取得: ページングあり GET /api/player/competition/9fa52404/ranking : expected([200]) != actual(500) tenant:qbbid-ifmst-1699538076 role:player playerID:9fa52407 competitionID:9fa52404 rankAfter:100
13:54:39.973893 整合性チェックを終了します
[ADMIN] 13:54:39.973898 Scenario:validation elapsed:3.521725123s
13:54:39.973901 整合性チェックに失敗しました
13:54:40.974138 ERROR[0] prepare: load-validation: GET /api/player/competition/9fa5252f/ranking : expected([200]) != actual(500) tenant:gr-wwxceh-1699538076 role:player playerID:9fa52401 competitionID:9fa5252f rankAfter:
13:54:40.974156 ERROR[1] prepare: load-validation: GET /api/player/competition/9fa52404/ranking : expected([200]) != actual(500) tenant:qbbid-ifmst-1699538076 role:player playerID:9fa52407 competitionID:9fa52404 rankAfter:100
[ADMIN] 13:54:40.974291 ScenarioScoreMap: map[string]int64{
  "AdminBilling":            0,
  "AdminBillingValidate":    0,
  "OrganizerNewTenant":      0,
  "OrganizerPeacefulTenant": 0,
  "OrganizerPopularTenant":  0,
  "Player":                  0,
  "PlayerValidate":          0,
  "TenantBillingValidate":   0,
}
[ADMIN] 13:54:40.974397 WorkerCount: map[string]int{}
13:54:40.974516 Error 2 (Critical:0)
[ADMIN] 13:54:40.974596 ScenarioCount: map[bench.ScenarioTag]string{
  "AdminBilling":            "count: 0 (error: 0)",
  "AdminBillingValidate":    "count: 0 (error: 0)",
  "OrganizerNewTenant":      "count: 0 (error: 0)",
  "OrganizerPeacefulTenant": "count: 0 (error: 0)",
  "OrganizerPopularTenant":  "count: 0 (error: 0)",
  "Player":                  "count: 0 (error: 0)",
  "PlayerValidate":          "count: 0 (error: 0)",
  "TenantBillingValidate":   "count: 0 (error: 0)",
}
13:54:40.974623 PASSED: false
13:54:40.974629 SCORE: 0 (+0 0(2%))
[ADMIN] 13:54:40.974776 score.ScoreTable{
  "GET /api/admin/tenants/billing":                         0,
  "GET /api/organizer/billing":                             0,
  "GET /api/player/competition/:competition_id/ranking":    0,
  "GET /api/player/competitions":                           0,
  "GET /api/player/player/:player_name":                    0,
  "POST /api/admin/tenants/add":                            0,
  "POST /api/organizer/competition/:competition_id/finish": 0,
  "POST /api/organizer/competition/:competition_id/score":  0,
  "POST /api/organizer/competitions/add":                   0,
  "POST /api/organizer/player/:player_name/disqualified":   0,
  "POST /api/organizer/players/add":                        0,
}
```
結果は変わらず、rankingのところでエラー発生。
本日は、オリジナルのテーブルをもとに戻して終えました。

---
#### SQLコマンド
参考にしたページは[よく使うMySQLコマンド&構文集](https://qiita.com/CyberMergina/items/f889519e6be19c46f5f4)です。
##### ログイン
```bash
# localhostのMySQLサーバに接続する場合
$ mysql -u [ユーザー名] -p

# localhostのMySQLサーバに接続する場合（ワンラインでパスワードまで渡す）
$ mysql -u [ユーザー名] -p[パスワード ※ 平文で渡すとコマンド履歴にパスワードが載ってしまうので避けましょう]

# 外部MySQLサーバに接続する場合
$ mysql -u [ユーザー名] -p -h [host名] -P [ポート番号]
```
##### ログアウト
```bash
mysql > \q
mysql > quit
mysql > exit
```

##### データベース関連
```bash
# データベース一覧の表示
mysql > show databases;
# データベースの追加(test_dbを追加する場合)
mysql > create database test_db;
# データベースの選択(test_dbを選択する場合)
mysql > use test_db;
```

##### テーブル関連
```bash
# テーブル一覧の表示
mysql > show tables;
# テーブル一覧の表示　もっと詳細が知りたい場合
mysql > show table status;
# 全テーブルから特定のフィールド検索
mysql > SELECT table_name, column_name FROM information_schema.columns WHERE column_name = [検索条件];
# テーブルの作成
mysql > CREATE TABLE [テーブル名] (
  [フィールド名] [データ型] [オプション]
) ENGINE=[InnoDB/MyISAM] DEFAULT CHARSET=[文字コード];
# テーブルの削除
mysql > DROP TABLE [テーブル名]
# テーブルの削除　TABLEが存在しない時にエラーで止めたくなければ
mysql > DROP TABLE IF EXISTS [テーブル名]
# テーブル名の変更
mysql > ALTER TABLE [旧テーブル名] RENAME [新テーブル名]
# テーブルにカラムの追加
mysql > ALTER TABLE [テーブル名] ADD [追加カラム名] [型] [必要であればオプション等];
# テーブル設計の確認
mysql > desc [テーブル名]
+------------------+--------------+------+-----+---------+----------------+
| Field            | Type         | Null | Key | Default | Extra          |
+------------------+--------------+------+-----+---------+----------------+
| id               | int(11)      | NO   | PRI | NULL    | auto_increment |
| user_name        | varchar(100) | NO   |     | NULL    |                |
| mail_address     | varchar(200) | NO   |     | NULL    |                |
| password         | varchar(100) | NO   |     | NULL    |                |
| created          | datetime     | YES  |     | NULL    |                |
| modified         | datetime     | YES  |     | NULL    |                |
+------------------+--------------+------+-----+---------+----------------+
# テーブル設計の確認　もっと詳細が知りたい場合
mysql > SHOW FULL COLUMNS FROM [テーブル名];
+------------------+--------------+-----------------+------+-----+---------+----------------+---------------------------------+----------------+
| Field            | Type         | Collation       | Null | Key | Default | Extra          | Privileges                      | Comment        |
+------------------+--------------+-----------------+------+-----+---------+----------------+---------------------------------+----------------+
| id               | int(11)      | NULL            | NO   | PRI | NULL    | auto_increment | select,insert,update,references | ID             |
| user_name        | varchar(100) | utf8_general_ci | NO   |     | NULL    |                | select,insert,update,references | ユーザー名     |
| mail_address     | varchar(200) | utf8_general_ci | NO   |     | NULL    |                | select,insert,update,references | メールアドレス |
| password         | varchar(100) | utf8_general_ci | NO   |     | NULL    |                | select,insert,update,references | パスワード     |
| created          | datetime     | NULL            | YES  |     | NULL    |                | select,insert,update,references | 登録日         |
| modified         | datetime     | NULL            | YES  |     | NULL    |                | select,insert,update,references | 更新日         |
+------------------+--------------+-----------------+------+-----+---------+----------------+---------------------------------+----------------+
```
