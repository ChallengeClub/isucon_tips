# 必要な時だけ行うGo計測

対象環境のGoバージョン、実行ファイル、計測経路、負荷条件、保存先を先に確認する。これはコマンドの例で、対象パス・ポート・時間は実環境に合わせる。下記を順に全部実行する手順ではない。

## 稼働サービス

pprofが利用可能か、ルート登録と待受アドレスを確認する。404だけでアプリ全体に計測機能がないと断定せず、別ポート・パスも実装から確認する。

利用可能なら、CPU、heap、allocs、goroutine、mutex/block等のうち症状に対応するものだけを取得する。mutex/blockは計測の有効化が必要な場合がある。CPU profileはI/O待ちの全体像を示さない。goroutineの待機や要求区間・DB時間も併用する。heapの保持量とallocsの累積割り当て量を区別する。

```bash
curl --fail --max-time 25 'http://127.0.0.1:PORT/debug/pprof/profile?seconds=10' -o PRIVATE_DIR/cpu.pprof
go tool pprof -top APP_BINARY PRIVATE_DIR/cpu.pprof
```

計測は負荷走行の対象期間に合わせ、初期化・事前検証だけを測った結果と区別する。バイナリとprofileの対応、取得時刻、計測による負荷を記録する。

エンドポイントを追加する場合は依頼範囲内で必要な最小変更とし、loopbackへのbindとSSHトンネル等を使う。公開向けmuxへの安易な登録や新しい外部公開ポートは避ける。計測負荷を止め、変更した設定の扱いも記録する。

## 局所ベンチ

計測で特定した関数・処理を比較する必要がある時に限り作る。実入力に近いデータ、結果の利用、準備時間の除外、同じハードウェア・Goバージョン・並行数を確認する。

```bash
go test -run='^$' -bench='BenchmarkTarget' -benchmem -count=6 ./TARGET_PACKAGE > PRIVATE_DIR/before.txt
# 比較する変更を適用し、同条件でafter.txtへ出力する
benchstat PRIVATE_DIR/before.txt PRIVATE_DIR/after.txt
```

回数は例で、残り時間とばらつきに合わせる。複数の計測を同一CPUで並列実行しない。Go 1.23等ではb.Nを使い、b.Loopは対応版を確認してから使う。benchstat未導入なら既存手段で比較するか、導入の必要性を判断する。競技中に@latestで依存物を無条件更新しない。

## 公式資料

- [Go diagnostics](https://go.dev/doc/diagnostics)
- [net/http/pprof](https://pkg.go.dev/net/http/pprof)
- [benchstat](https://pkg.go.dev/golang.org/x/perf/cmd/benchstat)
- [Go GC guide](https://go.dev/doc/gc-guide)

一般的な実装例は実環境のAPI・Goバージョンを確認して使う。既存のSQLや状態処理を変えずに、計測だけで得点改善したと報告しない。
