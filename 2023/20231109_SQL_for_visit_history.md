## やりたいこと
- vistit_historyの削減が上手くいかない問題の検証と解消
## 情報ソース
[ISUCON12 予選問題の解説と講評](https://isucon.net/archives/56850281.html): ISUCON公式Blog  
しかし、ここでこのクエリを発行している部分のアプリケーションの処理をよく見ると、実は visit_history テーブルの行は「各テナント/大会/参加者につき、最初のアクセス時に作成される1行のみが必要」ということが分かります。集約クエリで MIN(created_at) を取得して、その値しか使わないためです。
つまりこのテーブルには大量に不要な行が含まれているため、次のようなクエリで不要な行を消し去ることができます。
```
CREATETABLEvisit_history_2 ASSELECTtenant_id, player_id, competition_id, MIN(created_at) AScreated_at FROMvisit_history GROUPBYtenant_id, player_id, competition_id;
ALTERTABLEvisit_history RENAMETOvisit_history_old;
ALTERTABLEvisit_history_2 RENAMETOvisit_history;
CREATEUNIQUEINDEXvisit_history_idx ONvisit_history(tenant_id, player_id, competition_id);
```
MIN(created_at) の行だけを使って新しいテーブルを作成し、既存のテーブルと入れ換え、更にUNIQUE INDEX を貼ることができます。この処理を行うと、初期の320万行が20万行まで削減できます。
この visit_history へのINSERTはリーダーボードへの閲覧アクセス時に発生します。非常にリクエストが多いエンドポイントになるため、毎回INSERTする必要がなくなるのは嬉しいですね。
## ソース確認
/home/isucon/webapp/go/isuports.go
```go	
	// 大会ごとの課金レポートを計算する
	func billingReportByCompetition(ctx context.Context, tenantDB dbOrTx, tenantID int64, competitonID string) (*BillingReport, error) {
    // 略	
    // ランキングにアクセスした参加者のIDを取得する
	vhs := []VisitHistorySummaryRow{}
	if err := adminDB.SelectContext(
		ctx,
		&vhs,
		"SELECT player_id, MIN(created_at) AS min_created_at FROM visit_history WHERE tenant_id = ? AND competition_id = ? GROUP BY player_id",
		tenantID,
		comp.ID,
	); err != nil && err != sql.ErrNoRows {
		
	// 参加者向けAPI
	// GET /api/player/competition/:competition_id/ranking
	// 大会ごとのランキングを取得する
	func competitionRankingHandler(c echo.Context) error {
            // 略		
		    if _, err := adminDB.ExecContext(
		        ctx,
		        "INSERT INTO visit_history (player_id, tenant_id, competition_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
		        v.playerID, tenant.ID, competitionID, now, now,
		    ); err != nil {
```
- visit_historyに対する操作は、SELECT１箇所、INSERT1箇所。
- SELECTでupdated_atは使ってない。
- 以上からcompetitionIDの利用をやめればOK。具体的には下記。
```diff
--- a/go/isuports.go
+++ b/go/isuports.go
@@ -1342,8 +1342,8 @@ func competitionRankingHandler(c echo.Context) error {
 
 	if _, err := adminDB.ExecContext(
 		ctx,
-		"INSERT INTO visit_history (player_id, tenant_id, competition_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
-		v.playerID, tenant.ID, competitionID, now, now,
+		"INSERT INTO visit_history (player_id, tenant_id, competition_id, created_at) VALUES (?, ?, ?, ?)",
+		v.playerID, tenant.ID, competitionID, now,
 	); err != nil {
 		return fmt.Errorf(
 			"error Insert visit_history: playerID=%s, tenantID=%d, competitionID=%s, createdAt=%d, updatedAt=%d, %w",
```