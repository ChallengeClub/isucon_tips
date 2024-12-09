
# ISUCON14 当日の行動メモ (By ChatGPT)

---

### **10:12**
- iwasa: CloudFormation構築完了、サーバ情報共有。

### **10:21**
- 各OSでのホスト設定について指示を共有。
  - **Mac/Linux:** `/etc/hosts`
  - **Windows:** `C:\Windows\System32\drivers\etc\hosts`
  - **追加するホスト情報:**
    ```
    18.179.80.81 isuride.xiv.isucon.net
    52.194.131.50 isuride.xiv.isucon.net
    18.181.89.66 isuride.xiv.isucon.net
    ```

### **10:30**
- `WEBAPP`ディレクトリの容量を確認し、リポジトリに配置。  
  **容量詳細:**
  ```plaintext
  96M     ./nodejs
  53M     ./php
  44K     ./mysql
  84K     ./ruby
  1.4M    ./public
  39M     ./python
  5.3M    ./payment_mock
  7.3M    ./go
  59M     ./perl
  112K    ./nginx
  722M    ./rust
  828K    ./sql
  982M    .
  ```

### **10:39**
- ゆんたん: IPv6アドレスを共有。

### **10:54**
- tk: IPv4アドレスを共有。

### **10:57**
- ゆんたん: ベンチ・計測用サーバーのアクセス情報を共有:
- 公開鍵を受け取り、サーバーに登録する準備を実施。

### **10:59**
- iwasa: 公開鍵（`id_rsa_kiwsa.pub`）を共有。

### **11:06**
- iwasa: サーバー確認用コマンドを共有。
  ```bash
  $ cat /etc/os-release                   # OS確認
  $ grep -v nologin /etc/passwd           # ユーザー確認
  $ sudo lsof -P -i | grep -v sshd        # プロセス確認
  $ sudo ss -tlp | grep hoge              # プロセス確認
  $ systemctl list-unit-files -t service  # 有効なサービス確認
  ```

### **11:12**
- ゆんたん: AWS EC2上にベンチ・計測用サーバーを再構築。アクセス情報を更新:

### **11:15**
- iwasa: `pprotain`が正常に動作。

### **11:54**
- tk: 公開鍵（`id_rsa.pub`）を共有。

### **11:26**
- iwasaがインスタンス1、ゆんたんがインスタンス2、tkがインスタンス3で作業開始。
- tkがiwasaさんのCodespaceで作業開始。

### **11:39**
- iwasaが`pprotain`を導入し、Webモニタリング環境を整備。

### **11:51**
- ビルドとデプロイ環境を整備完了。
#### コマンド共有：
```bash
cd ansible
ansible-playbook -i inventory.yaml -u ubuntu build_and_deploy.yaml
```
### **12:03**
- `pprof`のポートを開放し、性能測定環境を構築。
- SQLログを取得し、問題のクエリを特定。

### **12:15 - 12:23**
- `pt-query-digest`を使用してクエリプロファイルを作成。ChatGPTで解析し、改善案を検討。

### **12:30 - 13:00**
- メンバー全員が昼休憩に入り、各自で昼食をとる。

### **13:02**
- MySQLのデータベース確認を実施。

### **13:19**
- GitHubの過去コードを参考にクエリ改善方針を共有。

### **14:33**
- SQLインデックスのテストを開始。

#### **成果:**  
スコア3457点まで向上。
```sql
CREATE INDEX idx_chairs_access_token ON chairs (access_token);
CREATE INDEX idx_rides_user_id_created_at ON rides (user_id, created_at);
```

### **14:45**
- 改善されたSQLインデックスを最終適用。

### **15:19**
- `ownerGetChairs`の修正完了。スコア3611達成。

### **15:44**
- ビルド・デプロイ手順を最終整備。
```bash
cd webapp/go
go build -o isuride
cd ansible
ansible-playbook -i inventory.yaml -u ubuntu build_and_deploy.yaml
```

### **16:30**
- `/api/chair/notification`のコードを更新し、API対応を完了。

### **16:45以降**
- **最終調整:**
  - MySQLのスロークエリログを無効化。
    ```conf
    slow_query_log = 0
    ```
  - セキュリティグループ設定など、競技環境のトラブルシュートを実施。
---

## **総括**
- **スコア推移:** 初期1845 → 最終3611
- **成功要因:**
  - モニタリング、ビルド&デプロイ環境の構築。
  - SQLインデックス最適化によるクエリ改善。
  - チーム内での効率的な情報共有とタスク分担。
