# 日本語の入力テスト
## wsl2でのisucon12環境のtips
- wsl2の/etc/hostsに登録されているisucon関係のアドレスをeth0のものと一致させないとbenchが成功しない
- prometheusは、wsl2のeth0のアドレスで呼び出す。例: http://172.26.40.218:9090/
