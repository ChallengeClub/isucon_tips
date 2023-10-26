# webappをgithub登録
## 大枠の手順
- githubのWeb UIでリポジトリを作る
- AWS上のVMから`git push`

## 手順詳細
- ~/.gitconfigの設定
  - `git config --global user.email "isucon@test"`
  - `git config --global user.name "isucon"`
  - `git config --global init.defaultBranch main`
- リポジトリ作成とソース登録
  - `git init`
  - `git add *`
  - `git status`
  - `commit -m "first commit"`
  - `git log`
- remoteの設定
  - `git remote add origin https://github.com/HideakiTakechi/isucon12q.git`
- remoteへpush
  - `git push`
    - main/master不整合でエラーになる場合は`git push origin main`にする
    - [Gitのデフォルトブランチをmasterからmainに変更する方法](https://qiita.com/fk_chang/items/a4839a595fef9a2c3724)も参照しよう
- 認証
  - git urlはsshでなくhttpsでも認証できる
  - httpsでの認証で使うアクセストークンの使用方法が変わった
    - https://qiita.com/seigot/items/605661666f074547a89e
    - アクセストークンの有効期限はISUCON本番まで持つはず！

# ディレクトリ容量の確認
- `du -sh *`

# 共同作業時の掛け声
- 飛行機のパイロット方式: "I have control!" "You have Control!"
- 日本語方式: 「お願いします！」

