ISUCON本の3章に倣い、mysqlでslowlogを出力する設定にしてDBのチューニング手順を試す
## slowlogを出力するように設定変更
/etc/mysql/my.cnfに設定するらしいので様子をみる
```bash
$ cd /etc/mysql
$ cat my.cnf
(中略)
!includedir /etc/mysql/conf.d/
!includedir /etc/mysql/mysql.conf.d/
```
どうもmy.cnfに直接書くのではなく、サブディレクトリに置いたファイルを読み込むスタイルらしい
```bash
$ grep mysqld conf.d/* mysql.conf.d/*
conf.d/mysqldump.cnf:[mysqldump]
mysql.conf.d/mysqld.cnf:[mysqld]  <----- ここ！
mysql.conf.d/mysqld.cnf:# pid-file      = /var/run/mysqld/mysqld.pid
mysql.conf.d/mysqld.cnf:# socket        = /var/run/mysqld/mysqld.sock 
$ cd mysql.conf.d
$ vim mysqld.conf
```
ふむふむ、「ここ」に書くスタイルらしい。ここ(mysql.conf.d/mysqld.cnfを見ると、コメントアウトされたものを発見
```
mysql.conf.d/mysqld.cnf: ※抜粋
# Here you can see queries with especially long duration
# slow_query_log                = 1
# slow_query_log_file   = /var/log/mysql/mysql-slow.log
# long_query_time = 2
# log-queries-not-using-indexes
```
mysql.conf.d以下のファイルすべて読み込む説と、.cnfファイルだけ読み込む説があると教えてもらい、分からないので別ディレクトリにファイルをバックアップして編集
``` bash
$ sudo cp mysqld.cnf ../mysqld.cnf-orig
```
そして変更：
```
mysql.conf.d/mysqld.cnf: ※抜粋
# Here you can see queries with especially long duration
slow_query_log                = 1
slow_query_log_file   = /var/log/mysql/mysql-slow.log
long_query_time = 0
log-queries-not-using-indexes
```
log-queries-not-using-indexesと書かないとインデックスのないクエリが出ないのか。さて、mysqldをrestartして確認
```
$ sudo systemctl restart mysql
$ cd /var/log/mysql
-bash: cd: /var/log/mysql: Permission denied
```
おっとisuconユーザでも入れない。毎回面倒なのでパーミッション変更
```bash
$ ls -ld /var/log/mysql
drwxr-x--- 2 mysql adm 4096 Oct  6 00:00 /var/log/mysql
$ sudo vigr
こんな感じで編集
- adm:x:4:syslog,ubuntu
+ adm:x:4:syslog,ubuntu,isucon
ここでログインしなおす
$ id
uid=1001(isucon) gid=1001(isucon) groups=1001(isucon),4(adm),27(sudo),122(docker)
admグループが追加されていることを確認
$ cd /var/log/mysql
$ ls
error.log mysql-slow.log
```
なんかでてる。

## benchを走らせてslowlogをmysqldumpslowで分析
```bash
$ cd
$ cd bench
$ ./bench -target-addr 127.0.0.1:443
中略
12:59:46.771339 SCORE: 3175 (+3175 0(0%))
[ADMIN] 12:59:46.771515 score.ScoreTable{
  "GET /api/admin/tenants/billing":                         6,
  "GET /api/organizer/billing":                             22,
  "GET /api/organizer/players/list":                        27,
  "GET /api/player/competition/:competition_id/ranking":    844,
  "GET /api/player/competitions":                           128,
  "GET /api/player/player/:player_name":                    618,
  "POST /api/admin/tenants/add":                            2,
  "POST /api/organizer/competition/:competition_id/finish": 37,
  "POST /api/organizer/competition/:competition_id/score":  49,
  "POST /api/organizer/competitions/add":                   39,
  "POST /api/organizer/player/:player_name/disqualified":   12,
  "POST /api/organizer/players/add":                        5,
}
$ sudo mysqldumpslow /var/log/mysql/mysql-slow.log

Reading mysql slow query log from /var/log/mysql/mysql-slow.log
Count: 1  Time=3.59s (3s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  DELETE FROM visit_history WHERE created_at >= 'S'

Count: 1298  Time=0.09s (117s)  Lock=0.00s (0s)  Rows=89.9 (116720), isucon[isucon]@localhost
  SELECT player_id, MIN(created_at) AS min_created_at FROM visit_history WHERE tenant_id = N AND competition_id = 'S' GROUP BY player_id

Count: 7  Time=0.03s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  INSERT INTO tenant (name, display_name, created_at, updated_at) VALUES ('S', 'S', N, N)

Count: 897  Time=0.01s (6s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  INSERT INTO visit_history (player_id, tenant_id, competition_id, created_at, updated_at) VALUES ('S', N, 'S', N, N)

Count: 1  Time=0.01s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  UPDATE id_generator SET id=N WHERE stub='S'

Count: 9385  Time=0.01s (51s)  Lock=0.00s (34s)  Rows=0.0 (0), isucon[isucon]@localhost
  REPLACE INTO id_generator (stub) VALUES ('S')

Count: 1  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  DELETE FROM tenant WHERE id > N

Count: 1  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=1.0 (1), isucon[isucon]@localhost
  select @@version_comment limit N

Count: 1937  Time=0.00s (1s)  Lock=0.00s (0s)  Rows=1.0 (1919), isucon[isucon]@localhost
  SELECT * FROM tenant WHERE name = 'S'

Count: 10  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=104.9 (1049), isucon[isucon]@localhost
  SELECT * FROM tenant ORDER BY id DESC

Count: 897  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=1.0 (897), isucon[isucon]@localhost
  SELECT * FROM tenant WHERE id = N

Count: 29285  Time=0.00s (1s)  Lock=0.00s (0s)  Rows=4.1 (119536), isucon[isucon]@localhost
  #

Count: 14421  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), 0users@0hosts
  administrator command: Prepare

Count: 443  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), 0users@0hosts
  administrator command: Quit

Count: 14421  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), 0users@0hosts
  administrator command: Close stmt
```
Countはその同じクエリが実行された回数。各項目のカッコ内は全実行の合計、カッコのついていないのは平均値。
最初の3秒かかっているDELETEはbenchの初期化処理らしいのでパスして、visit_historyテーブルのクエリを攻めてみよう。2つめのこれ↓
```
Count: 1298  Time=0.09s (117s)  Lock=0.00s (0s)  Rows=89.9 (116720), isucon[isucon]@localhost
  SELECT player_id, MIN(created_at) AS min_created_at FROM visit_history WHERE tenant_id = N AND competition_id = 'S' GROUP BY player_id
```
全体で2分くらいかかってる（相手にとって不足なし）。ここで、benchをもう一回実行して、scoreのばらつきを確認。。。結構ばらつきがある（ト書きのみでスミマセン）

## DBのチューニング手順を試してみる
```
$ mysql -u isucon -p
Enter password: isucon
mysql> show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| isuports           |
| performance_schema |
+--------------------+
3 rows in set (0.08 sec)

mysql> use isuports
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Database changed
mysql> show tables;
+--------------------+
| Tables_in_isuports |
+--------------------+
| id_generator       |
| tenant             |
| visit_history      |
+--------------------+
3 rows in set (0.00 sec)

mysql> show create table visit_history;
+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Table         | Create Table

                                                                                               |
+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| visit_history | CREATE TABLE `visit_history` (
  `player_id` varchar(255) NOT NULL,
  `tenant_id` bigint unsigned NOT NULL,
  `competition_id` varchar(255) NOT NULL,
  `created_at` bigint NOT NULL,
  `updated_at` bigint NOT NULL,
  KEY `tenant_id_idx` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci |
+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
1 row in set (0.00 sec)
```
tenant_idにだけインデックスが張ってある。それにcompetition_idってidなのに255文字の文字列型ってどうなの。player_idもか。
```
mysql> select count(*) from visit_history;
+----------+
| count(*) |
+----------+
|  3225652 |
+----------+
1 row in set (1.16 sec)
```
300万レコードもある！
EXPLAINでDBエンジンの計画を調べてみる。
tenant_id = NのNは何か数字に置き換える。最初0にしたらrows(なめるレコード数)が小さかった。1にすると148万行もなめている。数を変えるごとにrowが大きくばらつく（画面を取り損ねたのでト書きだけですみません）。だから平均89.9レコードしかなめてないのに全体で2分かかっているのかも
```
mysql> EXPLAIN SELECT player_id, MIN(created_at) AS min_created_at FROM visit_history WHERE tenant_id = 1 AND competition_id = 'S' GROUP BY player_id;
+----+-------------+---------------+------------+------+---------------+---------------+---------+-------+---------+----------+------------------------------+
| id | select_type | table         | partitions | type | possible_keys | key           | key_len | ref   | rows    | filtered | Extra                        |
+----+-------------+---------------+------------+------+---------------+---------------+---------+-------+---------+----------+------------------------------+
|  1 | SIMPLE      | visit_history | NULL       | ref  | tenant_id_idx | tenant_id_idx | 8       | const | 1484299 |    10.00 | Using where; Using temporary |
+----+-------------+---------------+------------+------+---------------+---------------+---------+-------+---------+----------+------------------------------+
1 row in set, 1 warning (0.00 sec)
```
効果がいまいち期待できないなか、他にめぼしい獲物クエリもないので、このクエリ向けに複合インデクスを張ってみる
```
mysql> alter table visit_hisotory add index tenant_id_competition_id_idx(tenant_id, competition_id);
ERROR 1146 (42S02): Table 'isuports.visit_hisotory' doesn't exist
mysql> alter table visit_history add index tenant_id_competition_id_idx(tenant_id, competition_id);
Query OK, 0 rows affected (22.07 sec)
Records: 0  Duplicates: 0  Warnings: 0

mysql> show create table visit_history;
+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Table         | Create Table


                                                              |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| visit_history | CREATE TABLE `visit_history` (
  `player_id` varchar(255) NOT NULL,
  `tenant_id` bigint unsigned NOT NULL,
  `competition_id` varchar(255) NOT NULL,
  `created_at` bigint NOT NULL,
  `updated_at` bigint NOT NULL,
  KEY `tenant_id_idx` (`tenant_id`),
  KEY `tenant_id_competition_id_idx` (`tenant_id`,`competition_id`) <------ここが追加された
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
1 row in set (0.00 sec)
```
見やすいようにEXPLAINのbefore after
```
もともと
mysql>  explain SELECT player_id, MIN(created_at) AS min_created_at FROM visit_history WHERE tenant_id = 1 AND competition_id = 'S' GROUP BY player_id;
+----+-------------+---------------+------------+------+---------------+---------------+---------+-------+---------+----------+------------------------------+
| id | select_type | table         | partitions | type | possible_keys | key           | key_len | ref   | rows    | filtered | Extra                        |
+----+-------------+---------------+------------+------+---------------+---------------+---------+-------+---------+----------+------------------------------+
|  1 | SIMPLE      | visit_history | NULL       | ref  | tenant_id_idx | tenant_id_idx | 8       | const | 1484299 |    10.00 | Using where; Using temporary |
+----+-------------+---------------+------------+------+---------------+---------------+---------+-------+---------+----------+------------------------------+
1 row in set, 1 warning (0.00 sec)
複合インデックスを張った後
mysql> explain SELECT player_id, MIN(created_at) AS min_created_at FROM visit_history WHERE tenant_id = 1 AND competition_id = 'S' GROUP BY player_id;
+----+-------------+---------------+------------+------+--------------------------------------------+------------------------------+---------+-------------+------+----------+-----------------+
| id | select_type | table         | partitions | type | possible_keys                              | key
                 | key_len | ref         | rows | filtered | Extra           |
+----+-------------+---------------+------------+------+--------------------------------------------+------------------------------+---------+-------------+------+----------+-----------------+
|  1 | SIMPLE      | visit_history | NULL       | ref  | tenant_id_idx,tenant_id_competition_id_idx | tenant_id_competition_id_idx | 1030    | const,const |    1 |   100.00 | Using temporary |
+----+-------------+---------------+------------+------+--------------------------------------------+------------------------------+---------+-------------+------+----------+-----------------+
1 row in set, 1 warning (0.00 sec)
```
複合インデックスが使われていて、148万行なめていたのが1行に減った。

## 再度ベンチマーク実行
```bash
$ cd bench
$ ./bench -target-addr 127.0.0.1:443
中略
13:57:08.593052 SCORE: 3084 (+3084 0(0%))
[ADMIN] 13:57:08.593182 ScenarioCount: map[bench.ScenarioTag]string{
  "AdminBilling":                      "count: 2 (error: 0)",
  "AdminBillingValidate":              "count: 5 (error: 0)",
  "OrganizerNewTenant":                "count: 2 (error: 0)",
  "OrganizerPeacefulTenant":           "count: 0 (error: 0)",
  "OrganizerPopularTenant":            "count: 1 (error: 0)",
  "OrganizerPopularTenantHeavyTenant": "count: 1 (error: 0)",
  "Player":                            "count: 77 (error: 0)",
  "PlayerHeavyTenant":                 "count: 6 (error: 0)",
  "PlayerValidate":                    "count: 11 (error: 0)",
  "TenantBillingValidate":             "count: 1 (error: 0)",
}
[ADMIN] 13:57:08.593208 score.ScoreTable{
  "GET /api/admin/tenants/billing":                         23,
  "GET /api/organizer/billing":                             20,
  "GET /api/organizer/players/list":                        29,
  "GET /api/player/competition/:competition_id/ranking":    784,
  "GET /api/player/competitions":                           124,
  "GET /api/player/player/:player_name":                    564,
  "POST /api/admin/tenants/add":                            3,
  "POST /api/organizer/competition/:competition_id/finish": 36,
  "POST /api/organizer/competition/:competition_id/score":  49,
  "POST /api/organizer/competitions/add":                   41,
  "POST /api/organizer/player/:player_name/disqualified":   10,
  "POST /api/organizer/players/add":                        6,
```
誤差が大きかったので効果があったのか不明。。。今日はこのくらいにしといたるわwww
