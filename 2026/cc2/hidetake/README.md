# cc2/hidetake

個人の検討・試行と、利用者・LLMが作業を再開するための補足を保存します。ここにある方針はチーム未承認です。
公開リポジトリの一部なので、秘密情報・実インスタンスの接続情報・生ログ・競技中の攻略情報は置きません。

- [再構築メモ](WORKSPACE-RECOVERY.md)：別の対象環境でworkspaceを用意するときに必要な前提と、復旧上の注意。
- [練習の引き継ぎ](PRACTICE-TRANSFER.md)：ISUCON13で経験したフロー・素材・速度感と、次の対象で確認する差分。
- [ISUCON14開始メモ](ISUCON14-START.md)：別workspaceを準備し、旧素材を選んで次の練習を始める手順。
- [ISUCON13移行手順](ISUCON13-START.md)：新workspace・EC2・SSHの利用者向け準備と、新セッションへの引き継ぎ。
- [個人PLAYBOOK](PLAYBOOK.md)：チーム版作成前の草案。現行の運用案は[team/PLAYBOOK.md](../team/PLAYBOOK.md)を参照。
- [private-isu参考例](examples/private-isu/README.md)：deploy・復旧と、準備／手動採取／復元を分けた計測の実装・知見。例外的なbackend言語に依存し、Go向けの汎用実装ではありません。
- [ISUCON13参考例](examples/isucon13/README.md)：Go build・binary deploy/rollback、nginx/MySQL/OSの計測を実証した素材。調整箇所を明示してISUCON14への移植に使い、移植効率は後で振り返ります。

再構築時はこの補足を指針にできますが、実際の対象・操作範囲を利用者と確認してください。
