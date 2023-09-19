# ベンチマーク素振り

[isucon12 参考](https://github.com/matsuu/aws-isucon/tree/main/isucon12-qualify#bench)

## t3.microで実行
```
$ ./bench -target-addr 127.0.0.1:443
~~~
[ADMIN] 13:01:19.069510 ScenarioScoreMap: map[string]int64{
  "AdminBilling":            0,
  "AdminBillingValidate":    0,
  "OrganizerNewTenant":      10,
  "OrganizerPeacefulTenant": 0,
  "OrganizerPopularTenant":  27,
  "Player":                  14,
  "PlayerValidate":          26,
  "TenantBillingValidate":   20,
}
[ADMIN] 13:01:19.272025 WorkerCount: map[string]int{
  "AdminBillingScenarioWorker":   1,
  "AdminBillingValidateWorker":   1,
  "NewTenantScenarioWorker":      1,
  "PlayerScenarioWorker":         4,
  "PlayerValidateScenarioWorker": 1,
  "PopularTenantScenarioWorker":  1,
  "TenantBillingValidateWorker":  1,
}
[ADMIN] 13:01:19.272084 ScenarioCount: map[bench.ScenarioTag]string{
  "AdminBilling":            "count: 1 (error: 0)",
  "AdminBillingValidate":    "count: 2 (error: 1)",
  "OrganizerNewTenant":      "count: 2 (error: 1)",
  "OrganizerPeacefulTenant": "count: 0 (error: 0)",
  "OrganizerPopularTenant":  "count: 1 (error: 1)",
  "Player":                  "count: 6 (error: 3)",
  "PlayerValidate":          "count: 1 (error: 1)",
  "TenantBillingValidate":   "count: 2 (error: 1)",
}
13:01:19.373752 Error 10 (Critical:2)
13:01:19.411493 PASSED: true
13:01:19.411521 SCORE: 70 (+97 -27(28%))
[ADMIN] 13:01:20.623075 score.ScoreTable{
  "GET /api/admin/tenants/billing":                         0,
  "GET /api/organizer/billing":                             0,
  "GET /api/organizer/players/list":                        2,
  "GET /api/player/competition/:competition_id/ranking":    12,
  "GET /api/player/competitions":                           7,
  "GET /api/player/player/:player_name":                    6,
  "POST /api/admin/tenants/add":                            3,
  "POST /api/organizer/competition/:competition_id/finish": 0,
  "POST /api/organizer/competition/:competition_id/score":  2,
  "POST /api/organizer/competitions/add":                   2,
  "POST /api/organizer/player/:player_name/disqualified":   0,
  "POST /api/organizer/players/add":                        0,
}
```

## c5.large に変更後に実行

```bash
$ ./bench -target-addr 127.0.0.1:443
~~~
[ADMIN] 13:15:03.129638 負荷走行を終了しました
[ADMIN] 13:15:04.129228 ScenarioScoreMap: map[string]int64{
  "AdminBilling":            4,
  "AdminBillingValidate":    105,
  "OrganizerNewTenant":      359,
  "OrganizerPeacefulTenant": 0,
  "OrganizerPopularTenant":  194,
  "Player":                  706,
  "PlayerValidate":          634,
  "TenantBillingValidate":   812,
}
[ADMIN] 13:15:04.129341 WorkerCount: map[string]int{
  "AdminBillingScenarioWorker":   1,
  "AdminBillingValidateWorker":   1,
  "NewTenantScenarioWorker":      1,
  "PlayerScenarioWorker":         64,
  "PlayerValidateScenarioWorker": 1,
  "PopularTenantScenarioWorker":  1,
  "TenantBillingValidateWorker":  1,
}
13:15:04.129358 Error 0 (Critical:0)
13:15:04.129360 PASSED: true
13:15:04.129364 SCORE: 2814 (+2814 0(0%))
[ADMIN] 13:15:04.129529 score.ScoreTable{
  "GET /api/admin/tenants/billing":                         7,
  "GET /api/organizer/billing":                             21,
  "GET /api/organizer/players/list":                        25,
  "GET /api/player/competition/:competition_id/ranking":    649,
  "GET /api/player/competitions":                           114,
  "GET /api/player/player/:player_name":                    527,
  "POST /api/admin/tenants/add":                            2,
  "POST /api/organizer/competition/:competition_id/finish": 34,
  "POST /api/organizer/competition/:competition_id/score":  48,
  "POST /api/organizer/competitions/add":                   38,
  "POST /api/organizer/player/:player_name/disqualified":   12,
  "POST /api/organizer/players/add":                        5,
}
```

スコアが上がっているのが分かる。CPU使用率は90%程度まで上がった。メモリは800MiB程度。

