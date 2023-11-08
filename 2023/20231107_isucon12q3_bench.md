# ISUCON12q3の整備を進めてベンチしてみた  
## 本日のサマリー  
- 整備残項目：dstat, ab導入、slow log有効化、/var/logアクセス性改善
- 攻略１：logrotate-->bench実施(2731)-->index追加-->bench実施(3381)
- 攻略２：visit_history削除（300万→20万）、エラーで切り戻し

## （整備残項目）
### dstat, ab導入
```
$ sudo apt -y install dstat
$ sudo apt -y install apache2-utils
```
※[10_install_packages.sh](https://github.com/ChallengeClub/isucon_tools/blob/main/10_install_packages.sh)にも反映

### slow log有効化
```
/etc/mysql/mysql.conf.d/mysqld.cnfを編集。
（/etc/mysql以下はバックアップ有り、編集して安全。）
※抜粋
# Here you can see queries with especially long duration
slow_query_log                = 1
slow_query_log_file   = /var/log/mysql/mysql-slow.log
long_query_time = 0
log-queries-not-using-indexes
```
```
$ sudo systemctl restart mysql
```
### /var/logアクセス性改善
/var/logなどの各種ログを見えるようにadmグループに各ユーザーを追加する。  
```
作業内容：
$ sudo vigr -s
こんな感じで編集
- adm:x:4:syslog,ubuntu
+ adm:x:4:syslog,ubuntu,isucon,hidetake,seigot,kiwasa,maleicacid,takaaki,nakamura,miteru
```
## （攻略１）
「[ISUCON12 予選問題の解説と講評]((https://isucon.net/archives/56850281.html))」と[10/24素振り](https://github.com/ChallengeClub/isucon_tips/blob/main/2023/20231024_study_isucon12q_review.md)を参考に攻略を試みました。
### logrotate
bench前にmysqlのログローテート実施（以下の操作でerror.logとmysql-slow.logとも対象）
```
/etc/logrotate.d/mysql-server
```
### bench実施
```
isucon@ip-172-31-13-26:~/bench$ ./bench -target-addr 127.0.0.1:443
中略
[ADMIN] 13:32:13.062787 負荷走行を終了しました
[ADMIN] 13:32:14.063969 ScenarioScoreMap: map[string]int64{
  "AdminBilling":            5,
  "AdminBillingValidate":    106,
  "OrganizerNewTenant":      338,
  "OrganizerPeacefulTenant": 0,
  "OrganizerPopularTenant":  195,
  "Player":                  645,
  "PlayerValidate":          671,
  "TenantBillingValidate":   771,
}
[ADMIN] 13:32:14.064078 WorkerCount: map[string]int{
  "AdminBillingScenarioWorker":   1,
  "AdminBillingValidateWorker":   1,
  "NewTenantScenarioWorker":      1,
  "PlayerScenarioWorker":         60,
  "PlayerValidateScenarioWorker": 1,
  "PopularTenantScenarioWorker":  1,
  "TenantBillingValidateWorker":  1,
}
13:32:14.064095 Error 0 (Critical:0)
13:32:14.064098 PASSED: true
13:32:14.064101 SCORE: 2731 (+2731 0(0%))
[ADMIN] 13:32:14.064272 score.ScoreTable{
  "GET /api/admin/tenants/billing":                         9,
  "GET /api/organizer/billing":                             20,
  "GET /api/organizer/players/list":                        26,
  "GET /api/player/competition/:competition_id/ranking":    612,
  "GET /api/player/competitions":                           116,
  "GET /api/player/player/:player_name":                    486,
  "POST /api/admin/tenants/add":                            2,
  "POST /api/organizer/competition/:competition_id/finish": 35,
  "POST /api/organizer/competition/:competition_id/score":  47,
  "POST /api/organizer/competitions/add":                   38,
  "POST /api/organizer/player/:player_name/disqualified":   12,
  "POST /api/organizer/players/add":                        5,
}
```
- その際のスローログ
```
isucon@ip-172-31-13-26:/var/log/mysql$ sudo mysqldumpslow /var/log/mysql/mysql-slow.log

Reading mysql slow query log from /var/log/mysql/mysql-slow.log
Count: 1  Time=3.39s (3s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  DELETE FROM visit_history WHERE created_at >= 'S'

Count: 1573  Time=0.08s (122s)  Lock=0.00s (0s)  Rows=87.7 (137911), isucon[isucon]@localhost
  SELECT player_id, MIN(created_at) AS min_created_at FROM visit_history WHERE tenant_id = N AND competition_id = 'S' GROUP BY player_id

Count: 7  Time=0.02s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  INSERT INTO tenant (name, display_name, created_at, updated_at) VALUES ('S', 'S', N, N)

Count: 1  Time=0.01s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  DELETE FROM tenant WHERE id > N

Count: 656  Time=0.01s (5s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  INSERT INTO visit_history (player_id, tenant_id, competition_id, created_at, updated_at) VALUES ('S', N, 'S', N, N)

Count: 9101  Time=0.01s (54s)  Lock=0.00s (42s)  Rows=0.0 (0), isucon[isucon]@localhost
  REPLACE INTO id_generator (stub) VALUES ('S')

Count: 1  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=1.0 (1), isucon[isucon]@localhost
  select @@version_comment limit N

Count: 1  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  UPDATE id_generator SET id=N WHERE stub='S'

Count: 1526  Time=0.00s (1s)  Lock=0.00s (0s)  Rows=1.0 (1525), isucon[isucon]@localhost
  SELECT * FROM tenant WHERE name = 'S'

Count: 13  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=105.3 (1369), isucon[isucon]@localhost
  SELECT * FROM tenant ORDER BY id DESC

Count: 656  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=1.0 (656), isucon[isucon]@localhost
  SELECT * FROM tenant WHERE id = N

Count: 27426  Time=0.00s (1s)  Lock=0.00s (0s)  Rows=5.1 (140092), isucon[isucon]@localhost
  #

Count: 13519  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), 0users@0hosts
  administrator command: Close stmt

Count: 388  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), 0users@0hosts
  administrator command: Quit

Count: 13519  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), 0users@0hosts
  administrator command: Prepare
```
### index追加
```
mysql> ALTER TABLE visit_history ADD INDEX tenant_id_idx_4(tenant_id, competition_id, player_id, created_at);
```
### 再bench実施
```
isucon@ip-172-31-13-26:~/bench$ sudo ./bench -target-addr 127.0.0.1:443
中略
[ADMIN] 13:54:48.218246 負荷走行を終了しました
[ADMIN] 13:54:49.218474 ScenarioScoreMap: map[string]int64{
  "AdminBilling":                      31,
  "AdminBillingValidate":              317,
  "OrganizerNewTenant":                528,
  "OrganizerPeacefulTenant":           0,
  "OrganizerPopularTenant":            195,
  "OrganizerPopularTenantHeavyTenant": 31,
  "Player":                            870,
  "PlayerHeavyTenant":                 18,
  "PlayerValidate":                    671,
  "TenantBillingValidate":             720,
}
[ADMIN] 13:54:49.218608 WorkerCount: map[string]int{
  "AdminBillingScenarioWorker":   1,
  "AdminBillingValidateWorker":   1,
  "NewTenantScenarioWorker":      2,
  "PlayerScenarioWorker":         95,
  "PlayerValidateScenarioWorker": 1,
  "PopularTenantScenarioWorker":  2,
  "TenantBillingValidateWorker":  1,
}
13:54:49.218623 Error 0 (Critical:0)
13:54:49.218627 PASSED: true
13:54:49.218630 SCORE: 3381 (+3381 0(0%))
[ADMIN] 13:54:49.218816 score.ScoreTable{
  "GET /api/admin/tenants/billing":                         32,
  "GET /api/organizer/billing":                             23,
  "GET /api/organizer/players/list":                        35,
  "GET /api/player/competition/:competition_id/ranking":    764,
  "GET /api/player/competitions":                           151,
  "GET /api/player/player/:player_name":                    627,
  "POST /api/admin/tenants/add":                            3,
  "POST /api/organizer/competition/:competition_id/finish": 41,
  "POST /api/organizer/competition/:competition_id/score":  56,
  "POST /api/organizer/competitions/add":                   47,
  "POST /api/organizer/player/:player_name/disqualified":   12,
  "POST /api/organizer/players/add":                        6,
}
```
- その際のスローログ
```
isucon@ip-172-31-13-26:~/bench$ sudo mysqldumpslow /var/log/mysql/mysql-slow.log

Reading mysql slow query log from /var/log/mysql/mysql-slow.log
Count: 1  Time=2.21s (2s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  DELETE FROM visit_history WHERE created_at >= 'S'

Count: 1  Time=0.02s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), debian-sys-maint[debian-sys-maint]@localhost
  FLUSH LOGS

Count: 8  Time=0.01s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  INSERT INTO tenant (name, display_name, created_at, updated_at) VALUES ('S', 'S', N, N)

Count: 806  Time=0.01s (5s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  INSERT INTO visit_history (player_id, tenant_id, competition_id, created_at, updated_at) VALUES ('S', N, 'S', N, N)

Count: 11322  Time=0.01s (61s)  Lock=0.01s (73s)  Rows=0.0 (0), isucon[isucon]@localhost
  REPLACE INTO id_generator (stub) VALUES ('S')

Count: 1  Time=0.01s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  DELETE FROM tenant WHERE id > N

Count: 1  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), isucon[isucon]@localhost
  UPDATE id_generator SET id=N WHERE stub='S'

Count: 4081  Time=0.00s (11s)  Lock=0.00s (0s)  Rows=130.8 (533780), isucon[isucon]@localhost
  SELECT player_id, MIN(created_at) AS min_created_at FROM visit_history WHERE tenant_id = N AND competition_id = 'S' GROUP BY player_id

Count: 35  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=106.2 (3717), isucon[isucon]@localhost
  SELECT * FROM tenant ORDER BY id DESC

Count: 1888  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=1.0 (1887), isucon[isucon]@localhost
  SELECT * FROM tenant WHERE name = 'S'

Count: 1  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=1.0 (1), isucon[isucon]@localhost
  select @@version_comment limit N

Count: 806  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=1.0 (806), isucon[isucon]@localhost
  SELECT * FROM tenant WHERE id = N

Count: 38649  Time=0.00s (1s)  Lock=0.00s (0s)  Rows=13.9 (536473), 2users@localhost
  #

Count: 18911  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), 0users@0hosts
  administrator command: Prepare

Count: 18911  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), 0users@0hosts
  administrator command: Close stmt

Count: 827  Time=0.00s (0s)  Lock=0.00s (0s)  Rows=0.0 (0), 0users@0hosts
  administrator command: Quit
```
- スコア：実施前(2731)-->index追加--実施後(3381)  
- index対象のスロークエリ：Count: 1573  Time=0.08s (122s)-->Count: 4081  Time=0.00s (11s) 
```
実施前
Count: 1573  Time=0.08s (122s)  Lock=0.00s (0s)  Rows=87.7 (137911), isucon[isucon]@localhost
  SELECT player_id, MIN(created_at) AS min_created_at FROM visit_history WHERE tenant_id = N AND competition_id = 'S' GROUP BY player_id
実施後
Count: 4081  Time=0.00s (11s)  Lock=0.00s (0s)  Rows=130.8 (533780), isucon[isucon]@localhost
  SELECT player_id, MIN(created_at) AS min_created_at FROM visit_history WHERE tenant_id = N AND competition_id = 'S' GROUP BY player_id
```

### isit_history削除（300万→20万）、エラーで切り戻し
（未記入）

- 気が付いたこと
    - isucon12qインスタンスでMySQLデータベースをフルリストアするscriptが見つからない。
    - DB初期化機能が入ってないなら、mysqldumpとかでDB保全しておくのが安全かも


