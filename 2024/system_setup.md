# システム構成とCICDフロー
![hight:100](images/system_setup.dio.svg)

- 競技開始
    - ポータルからテンプレートをダウンロード、AWSへインポートしてCloudFormation実行、ip address確定
    - .ssn/config設定、EC2ログイン試験(user=isucon)
    - inventory.yaml設定、ansible接続試験（test_connection.yaml）
    - ブラウザから対象サービス利用開始
    - ポータルから初回ベンチ実行（Discordへログをレポート）
- CICDフロー構築
    - インスタンス1のwebapp(/etcのコピー含む)をisucon14fへgit登録（直接pushでも手元環境へコピーしてpushでもOK）
    - 各自の開発環境でisucon14fをpull
    - ansible環境構築（setup_targets.yaml）、agentサービス起動、slowlogオン、nginxのtsv設定
    - main.goにpprotein計装、ビルドとデプロイ（build_and_deploy.yaml）、pprotein計測試験
    - ポータルから第２回ベンチ実行（Discordへログをレポート）
- Dev/CICD
    - devブランチでwebapp修正、ビルドとデプロイ（build_and_deploy.yaml）
    - ポータルから修正後ベンチ実行（Discordへログをレポート）
    - devブランチへcommit/push、プルリクエスト作成(dev->main,ベンチ点数を付記)
    - プルリクエストのマージ
- 最終リリース
    - 各インスタンスのソースコード更新（※goのbuild_and_deploy.yamlは実行ファイルのみ更新？）
    - 計測環境のリバート（agentサービス停止、slowlogオフ。pprotein計装コメントアウト。nginxログのオフ？）
    - 再起動試験(EC2の再起動、ベンチマーク)
