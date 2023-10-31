# 本日のサマリー
- おかしくなったサーバーをリセットしたので、細々とした設定を戻そうとした
- パッケージのインストールや設定変更は、シェルスクリプト化しようとした
- サーバーを設定するには、/etc/の編集が必要になった
- /etc/の編集を履歴管理できるように、webappのgitリポジトリに入れようとした
- 本番に備えて、githubのリポジトリとアカウントの運用を考え始めたら、学びが深かった
- 最終的に
  - webappと/etc/を、[kiwsさんのISUCON専用アカウント](https://github.com/kiws-isucon-bot)の[リポジトリ](https://github.com/kiws-isucon-bot/isucon12q3-testbot)にpushできた
  - シェルスクリプト2本を、[isucon_tools](https://github.com/ChallengeClub/isucon_tools)にpushできた

# TODO
- gitk over ssh
- `~isucon/isucon_tools/10-install-packages.sh`を`10_install_packages.sh`に`git mv`して`git push origin main`したら、ユーザー名とパスワードを聞かれてしまった…`~/.cache/git/credential/`が空だからか? 謎。
