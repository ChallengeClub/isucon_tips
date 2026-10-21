# ISUCON2026 CC2

## このディレクトリについて

CC2の3人で、チームの運用方針・手順・再利用するひな形を整備する場所です。
検討・実証を通じて、必要な内容から整備します。

ここは公開リポジトリです。秘密情報を置かず、対象固有の攻略記録は攻略ごとの非公開リポジトリ（`target/`）へ保存します。

## 用語

- workspace：各人のローカル作業フォルダ。Gitリポジトリではありません。
- target：workspace内の攻略用非公開Gitリポジトリ。対象サーバーとは別です。
- 対象サーバー：アプリ・DBが動くEC2。benchmarkサーバーと区別します。
- backend言語：実際に起動しているアプリの言語。webapp内の全言語を同時に配備する意味ではありません。

## 読む順番

1. このREADME：資料の入口と整備状況。
2. [チームPLAYBOOK案](team/PLAYBOOK.md)：運用の基本原則。チーム確認待ちの草案です。
3. [Gitワークフロー案](team/git-workflow.md)：ブランチ・commit・PR・mergeの運用案。
4. [RUNBOOK案](RUNBOOK.md)：共通の操作順序。具体的なコマンドは対象ごとに整備します。

開始時は[攻略開始チェックリスト](checklists/contest-start.md)、終了前は[終了前チェックリスト](checklists/final-check.md)を使用します。いずれもチーム確認待ちの草案です。

配置方針とその理由は[ADR 0001](decisions/0001-workspace-layout.md)、個人の検討案は[hidetake/](hidetake/README.md)を参照してください。

新しいworkspaceと対象別の操作手順は[templates](templates/README.md)から準備します。webapp・ubuntu・isucon、初期backend言語Goを想定し、稼働する言語はserviceで確認します。

## 資料の整備状況

| 資料 | 状況 |
|---|---|
| [チームPLAYBOOK](team/PLAYBOOK.md) | 草案。チーム確認待ち |
| [Gitワークフロー](team/git-workflow.md) | 草案。チーム確認待ち |
| [個人PLAYBOOK](hidetake/PLAYBOOK.md) | hidetakeの草案 |
| [RUNBOOK](RUNBOOK.md) | 草案。チーム確認待ち。対象別のコマンドは未整備 |
| [開始](checklists/contest-start.md)・[終了前](checklists/final-check.md)チェックリスト | 草案。チーム確認待ち |
| [templates](templates/README.md) | workspace・対象別操作手順のひな形。チーム確認待ち |
| [ADR 0001](decisions/0001-workspace-layout.md) | 配置方針の提案。チーム確認待ち |

## 現在の到達点と次の整備

private-isuで初回benchmark・配備・復旧を試行しました。ただしbackend言語が例外的に異なるため、実装は[hidetakeの参考例](hidetake/examples/private-isu/README.md)へ分離しました。Go向け配備と他問題のbenchmarkは未実装です。
利用者とLLMによる再開に必要なチーム未承認の補足は[再構築メモ](hidetake/WORKSPACE-RECOVERY.md)に保存しています。
次は必要に応じて、ログローテート付きbenchmark（8-4）、計装・ログ設定（8-5）、DB基本操作（8-6）を整備します。運用方針とひな形は引き続きチームで検討・実証します。

## 検討メモ

以下は既存の検討メモです。初動分担・準備項目・3台構成例は、チームで検討する案であり、採用済みの構成や確定した手順ではありません。

- 進め方と分担の方針
  - ひでたん、モリアイ、nuno8
```
              スタート
                   |
        +----------+----------+
        |          |          |
       A           B          C
    環境確認    コード読む    DB読む
    可視化計装
    ベンチ準備   API把握      Schema把握
        |          |          |
        +----------+----------+
                   |
              　　共有
```
　　その後、攻略が始まったら役割固定は余りしなくて良い

-攻略環境として用意しておくもの
   - 空のプライベートリポジトリ
（Ansible）
   - コードのデプロイ（３インスタンスにデプロイ、App再起動
   - 可視化の計装（node-expoter,pprofほか）
- ローカルからの操作として用意しておくもの
   - ベンチの実施、ログローテート、スタート
   - ローカル環境へのログの回収（ssh/SSM）

-環境の準備
  - AWSでCFn実行、EC2等が出来る。
  - EC2からPrivareリポジトリへソースコード登録。
  - 当日マニュアル読む
  - アプリケーションマニュアル読む（サービス仕様の把握）
  - チューニング候補箇所のピックアップ
  - 可視化準備
    - pprotein?
    - 1stベンチマーク 
  - チューニング
    - SQL関係（Index）
    - N+1
  - インスタンス構成の変更
  - 最初は３台同じものがくるだけ。ロードバランスするなら自分でnginx.conf設定。
```
              Benchmark
                   |
                Server1
                 nginx
                   |
             +-----+-----+
             |           |
          App#1        App#2
         Server1      Server2
             \           /
              \         /
                MySQL
               Server3
```


