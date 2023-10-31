# 本日のサマリー
- おかしくなったサーバーをリセットしたので、細々とした設定を戻そうとした
- パッケージのインストールや設定変更は、シェルスクリプト化しようとした
- サーバーを設定するには、/etc/の変更が必要になった
- /etc/の変更を履歴管理できるように、webappのgitリポジトリに入れようとした
- 本番に備えて、githubのリポジトリとアカウントの運用を考え始めたら、学びが深かった
- 最終的に、
  - webappと/etc/を、[kiwsさんのISUCON専用アカウント](https://github.com/kiws-isucon-bot)の[リポジトリ](https://github.com/kiws-isucon-bot/isucon12q3-testbot)にpushできた
  - シェルスクリプト2本を、[isucon_tools](https://github.com/ChallengeClub/isucon_tools)にpushできた
 
# Elastic IPでのアイスブレイク再び
「先週のElastic IPがなんちゃらって何ですか?」 -> 「EC2インスタンスに固定IPを関連付けたので、もうIPアドレス変わらないんですよ〜」<br>
「そのIPアドレスってどうやって確認するんですか?」 -> 「AWSにログインして、isucon12q3のElastic IPを見ると分かります〜」

確認したIPアドレスで、ログイン完了。

# 必要なパッケージのインストール
## 人間が使うツール
本番含め、慣れたツールが必要。
- ともさん: 慣れたエディタのemacsを入れたい。`sudo apt install emacs-nox`
- kiwsさん: gitkを入れたいが、パッケージ名が不明
```
$ gitk
Command 'gitk' not found, but can be installed with:
sudo apt install gitk
```

無いコマンドを入力すると、インストール方法が表示される。<br>
そこで、`sudo apt install gitk`を実行、インストールは成功。<br>
ところが、gitkを実行すると、
```
$ gitk
application-specific initialization failed: no display name and no $DISPLAY environment variable
Error in startup script: no display name and no $DISPLAY environment variable
    while executing
"load /usr/lib/x86_64-linux-gnu/libtk8.6.so"
    ("package ifneeded Tk 8.6.12" script)
    invoked from within
"package require Tk"
    (file "/usr/bin/gitk" line 10)
```

というエラーが発生。sshでログインしたCLIからは、(そのままでは)GUIは表示できない模様。TODO。

## Prometheus
[以前のtips](https://github.com/ChallengeClub/isucon_tips/blob/main/2023/20230921_node-exporter.md)より、
```
sudo apt -y install prometheus prometheus-node-exporter
```
を`~isucon/bin/10_install_packages.sh`に記入、実行。Prometheusがインストールされた。<br>
http://admin.t.isucon.local:9090/ にアクセスし、[呪文](https://github.com/ChallengeClub/isucon_tips/blob/main/2023/20230921_node-exporter.md#prometheus%E7%A2%BA%E8%AA%8D)を入力、Executeボタンを押し、グラフ表示も確認OK。

# /etc/の設定変更
次は[nginxの設定変更](https://github.com/ChallengeClub/isucon_tips/blob/main/2023/20230926_nginx_jsonLog.md)かと思ったが、設定変更をgithubで変更管理する提案あり。また、webappもgithubで管理する必要がある。<br>
本日のゴールとして、設定変更するか、github管理するかの2択となったが、設定変更するにはgithub管理する必要があるため、先にgithub管理を実施する方針となった。

# ISUCONにおけるgithub管理
議論の過程で、ISUCON当日のgithub共同作業において、アクセストークンをどうするか、アカウントとリポジトリをどうするか、といった検討が必要なことが判明。<br>
検索の結果、[ISUCONの先人の調査](http://tatamo.81.la/blog/2018/09/16/isucon8-qual-2/)が深い。みんなで読んで議論。
- bot用の専用githubアカウントを作る
- リポジトリは、
  - 作成した専用githubアカウントにリポジトリを作成しても、メンバー登録してChallengeClub内にリポジトリを作成しでもよい
  - /etc/内の重要情報の登録や、ISUCONレギュレーションでの共有不可から考えると、プライベートリポジトリにする
- 専用githubアカウントでアクセストークンを払い出す
  - ユーザーisuconがgit cloneするだけならアクセストークン不要だが、プライベートリポジトリで、かつ、ISUCON本番での初手がgit pushなので、アクセストークンが必要
  - 専用githubアカウントに加えて、個人のアカウントもメンバーに加えておけば、ローカルにcloneして個人のアカウントでpushもできる
  - ブランチ戦略は、小規模短時間が想定されるので、ブランチ無し、誰々さんブランチ、などが考えられるかも、要検討

という理解に至る。

なお、各人のgithubアカウントが分からなくなったので、[こちら](https://github.com/orgs/ChallengeClub/people)で確認。入れていなかった方の追加も行った。

## 休憩コラム〜gitでのユーザー管理とアクセス権設定〜
gitでのユーザー管理とアクセス権設定が話題に。MakerFaireでのARコンテンツ登録リポジトリは、以下の構成。
- gitのURLにsshを使用
- ユーザーgitだけを使用
  - ユーザーgitの~/.ssh/authorized_keysに、複数ユーザーのssh公開鍵を登録
- リポジトリは複数設置

簡単だが、リポジトリ単位のアクセス権設定ができない。<br>
[GitLab](https://gitlab.com/gitlab-org/gitlab)など高度な管理を備えたシステムの利用や、各ユーザー毎にauthorized_keysを設定するなどの方法もある。<br>
TODO: seigotさんに解説いただく。

## 専用githubアカウントの作成
githubのアカウント作成には、メールアドレスが必要。gmailには、アカウント名+サフィックス@gmail.com というエイリアスが作成できるとの[情報](https://mailwise.cybozu.co.jp/column/114.html)があり、実践。<br>
結果、同じメールボックスに来る別メールアドレスが作成できた。<br>
このメールアドレスを作って、[githubアカウント](https://github.com/kiws-isucon-bot)が作成できた。

## お試しリポジトリの作成とpush
### リポジトリの作成
専用githubアカウントで、[webappのリポジトリ](https://github.com/kiws-isucon-bot/isucon12q3-testbot)を、githubのWebUIで作成。

### アクセストークンの生成と保存
webappをgit pushする際に必要となる、アクセストークンの保存について議論。

git pushに備え、[githubのWebUIから、アクセストークンをClassicで生成](https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)。権限はreposのみ。期限は7日。

アクセストークンの保存は、[こちら](https://rfs.jp/server/git/github/personal_access_tokens.html)を見て検討した結果、以下の設定で30日間cacheに保存することにする。
```
git config --global credential.helper 'cache --timeout=2592000'
```

### シェルスクリプト化とwebappのpush
webapp丸ごとgithubに登録するか、議論。

まず、サイズを見る。
```
$ du -sh ~/webapp
445M	/home/isucon/webapp
````

445MB、登録できるサイズではある。

.gitignoreを調べると、
```
$ find ~/webapp -name '.gitignore'
/home/isucon/webapp/ruby/.gitignore
/home/isucon/webapp/sql/admin/.gitignore
/home/isucon/webapp/node/.gitignore
/home/isucon/webapp/php/var/cache/.gitignore
/home/isucon/webapp/php/.gitignore
/home/isucon/webapp/java/.gitignore
/home/isucon/webapp/tenant_db/.gitignore
/home/isucon/webapp/rust/.gitignore
/home/isucon/webapp/perl/.gitignore
/home/isucon/webapp/.gitignore
```

…となっており、既に必要な.gitignoreが運営の手によって設定されている。素晴らしい!<br>
例えば、tenant_dbは、dbもlockもignore対象。
```
$ cat ~/webapp/tenant_db/.gitignore
*.db
*.lock
```

よって、webapp丸ごとgithubに登録することにする。

[以前のtips](https://github.com/ChallengeClub/isucon_tips/blob/main/2023/20231019_webapp_to_github.md)を元に、先ほどのアクセストークンをcacheする設定も含めて、webappのgithubへの登録を[`~/bin/05_add_webapp_to_github.sh`](https://github.com/ChallengeClub/isucon_tools/blob/main/05_add_webapp_to_github.sh)でシェルスクリプト化。<br>
実行したところ、エラー発生。git statusで確認すると、git commitができていない。<br>
調べると、tipsで`git commit`とすべきところが、`commit`となっていて、それをコピペしたため、エラーが発生。<br>
tipsとともにスクリプトも修正。

手動でのgit commitが成功、続いてgit pushを実行したところ、ユーザー名とパスワードを聞かれる。<br>
ユーザー名は先ほど作成した専用アカウントのものを、パスワードは生成したアクセストークンを入力。<br>
結果、push成功!

### /etcのpush
/etc丸ごとgithubに登録するかどうか、議論。

判断のために、サイズを算出。大きくないので、丸ごと登録する。
```
$ sudo du -sh /etc
6.5M	/etc
```

rootでないとアクセスできないものがあるため、sudoして/etcをwebappにコピー。
```
sudo cp -a /etc ~/webapp/
```

ownerがrootのままのため、このままではユーザーisuconによるgit pushは失敗するはず。<br>
chownで、userとgroupをisucon:isuconに変更。
```
sudo chown -R isucon:isucon ~/webapp/etc
```

git addした後、git pushすれば、先ほどのアクセストークンがcacheされていて、認証情報を入力せずにpushできるはず。
```
$ cd ~/webapp
$ git add etc
 :(中略)
$ git commit -m "add etc"
 :(中略)
$ git push origin main
Enumerating objects: 1652, done.
Counting objects: 100% (1652/1652), done.
Compressing objects: 100% (1109/1109), done.
Writing objects: 100% (1651/1651), 799.35 KiB | 5.51 MiB/s, done.
Total 1651 (delta 119), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (119/119), completed with 1 local object.
To https://github.com/kiws-isucon-bot/isucon12q3-testbot.git
   ba09989..4dba3df  main -> main
```

push成功!

# スクリプトのisucon_toolsリポジトリ登録
ChallengeClubにkiws-isucon-botをメンバー登録すれば、ChallengeClub内のisucon_toolsにも、git pushできるはず。

まずは、ChallengeClubのメンバーにkiws-isucon-botを登録。

次に、remote側の更新が無いか、確認。
```
$ cd ~/git/isucon_tools
$ git fetch
$ git merge --ff-only
Already up to date.
```

問題ないため、本日作成の~/bin/*.shを ~/git/isucon_tools/にcp。続いて、git add。<br>
直接関連のない2つのスクリプトの登録だったので、commitは2つに分ける案もあったが、まぁいいやと丸っと1つでcommit。<br>
アクセストークンのcacheが効いており、パスワードを聞かれずにpush成功!

# TODO
- gitk over ssh
- アクセストークンのcacheが消えた?
  - `~isucon/isucon_tools/10-install-packages.sh`を`10_install_packages.sh`に`git mv`して`git push origin main`したら、ユーザー名とパスワードを聞かれてしまった。まだ30日はおろか、7日も経ってないのに! `~/.cache/git/credential/`が空だからか? 謎。
