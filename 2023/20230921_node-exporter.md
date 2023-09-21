![image](https://github.com/ChallengeClub/isucon_tips/assets/62125060/9db042b6-7130-4d90-b532-b0b3d1e8f7bb)ISUCON本の2章に倣い、prometheusを使用してモニタリング

## Prometheus のインストール。
```bash
$ apt -y install prometheus prometheus-node-exporter
```
aptでインストールすると、インストール直後に自動で実行されている。ネットワークのソケットの情報を出力するssコマンドで確認すると、prometheusが9090ポートで出力していることが分かる。

```bash
sudo ss -tlp | grep 
```

## AWSの設定変更
武知さんにセキュリティグループの変更をしていただき、9090ポートを開放してもらう。

## Prometheus確認
ブラウザで`http://{IPアドレス}:9090/`を開くと、GUIが表示される。
ここで、GUI上部のコンソールに以下を入力し、Excecuteするとグラフが表示される。
以下は、CPUの利用時間を1分ごとに出力するクエリ。
```
avg without(cpu) (rate(node_cpu_seconds_total{mode!="idle"}[1m]))
```

## ベンチマーク実行
```bash
$ cd bench
$ ./bench -target-addr 127.0.0.1:443
```
ベンチマーク実行されるが、EC2インスタンスがc3.microのままでは途中で処理が落ちてしまう。グラフはt5.largeにスケールしたときの実行例。

![image](https://github.com/ChallengeClub/isucon_tips/assets/62125060/69f200a0-3d6b-4554-912d-4f57a845ed9d)
