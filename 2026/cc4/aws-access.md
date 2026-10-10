# AWS操作: aws loginと限定ロールのAssumeRole

更新: 2026-10-10 JST。cc4は本番のAWS操作にこの方式を採用する方針。実行する操作・対象・時期はユーザー指示と当日マニュアルで確定する。この資料自体はEC2作成・停止・削除・権限拡張の実行許可ではない。

## 採用構成

自宅PC上のLinux VMでAWS CLIを動かす。認証のための常時起動EC2やIAM Identity Centerの導入は必須ではない。調査・配備は通常のSSHを継続し、AWS CLIはEC2自体の状態確認・許可された起動停止等に使う。SSMは必要時の代替経路。

```text
人間: 専用IAMユーザーでブラウザ認証
  → Linux VMのcodexユーザー: aws loginのログインキャッシュ
    → STS AssumeRole: 対象を限定した操作用ロール
      → EC2の参照・指定インスタンスの起動/停止、必要なSSM操作
```

## 認証元も限定する

~/.aws/configで限定ロールを指定するだけでは、認証元の直接利用を禁止できない。source_profileを直接指定したり、認証元で別のAssumeRoleを試すこともできる。人間の普段使いの管理者IAMユーザーを認証元として渡さない。

専用の認証元ユーザーには次だけを必要な範囲で付ける。
- aws login用: AWS管理ポリシーSignInLocalDevelopmentAccess。AWSサービスの管理権限ではなくログイン用トークンの発行を許可する。
- 指定した操作用ロールへのsts:AssumeRole。
- 自分のMFA登録・参照、必要な自分のパスワード変更。これらもIAM操作権限なので「AssumeRole以外は全て不可」とは表現しない。アカウント全体のIAM管理権限とは区別する。

グループ、他の付与ポリシー、ロールの信頼ポリシーも確認し、他の強いロールを利用できないかを人間が確認する。ロール側の信頼ポリシーは誰が引き受けられるか、権限ポリシーは引き受けた後に何ができるかを決める。

操作用ロールは対象EC2の起動/停止と必要な参照・SSM操作に限定する。EC2作成、削除、SG変更、IAM管理は現段階の既定範囲にしない。必要になった操作を説明して、人間がAWS側の権限と作業の許可を判断する。IAMで許可されていても競技規定で禁止された操作はしない。

## 人間が初回に用意するもの

1. IAMユーザー作成時にコンソールアクセスを有効にし、専用のパスワード・MFAを用意する。Identity Centerユーザーとは別。
2. 上記の認証元ポリシーと、操作用ロールの信頼・権限を設定する。
3. AWS CLI v2.32.0以降をLinux VMに用意する。SSMを使う場合はSession Manager pluginも別途用意する。
4. VMのcodexユーザーで次を実行し、ブラウザでは必ず専用ユーザーを選ぶ。既存の管理者セッションを選択しない。
```sh
aws login --profile cc4-practice --region ap-northeast-1
```
別端末のブラウザを使う場合は--remoteを追加し、人間が表示された案内に従う。認証コードやトークンをGitやチャットへ保存しない。
5. 意図したIAMユーザーになったかを確認する。
```sh
aws sts get-caller-identity --profile cc4-practice --region ap-northeast-1
```

MFA登録にはiam:CreateVirtualMFADeviceと、自分のユーザーに対するEnableMFADevice、GetUser、GetMFADevice、ListMFADevices等が必要。仮想MFA名をユーザー名に基づく範囲に絞る場合は、その命名規則で登録する。パスワード変更は自分のiam:ChangePasswordとiam:GetAccountPasswordPolicy。広いIAMFullAccessやアクセスキー発行権限はこの方式の必須条件ではない。解除・削除を任せるかは登録許可と別に決める。MFA登録済みという事実と、APIでMFA条件を強制できていることも別。aws loginとAssumeRoleの組み合わせで条件の動作を確認してから採用する。

## 起動停止のポリシー例

次は説明用の架空値。人間が対象のアカウントとインスタンスARNへ置き換える。Sidは任意の識別名であり、なくても動く。指定する場合はポリシー内で一意にする。

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ec2:DescribeInstances", "ec2:DescribeInstanceStatus"],
      "Resource": "*",
      "Condition": {
        "StringEquals": {"aws:RequestedRegion": "ap-northeast-1"}
      }
    },
    {
      "Effect": "Allow",
      "Action": ["ec2:StartInstances", "ec2:StopInstances"],
      "Resource": [
        "arn:aws:ec2:ap-northeast-1:123456789012:instance/i-0123456789abcdef0",
        "arn:aws:ec2:ap-northeast-1:123456789012:instance/i-0fedcba9876543210"
      ]
    }
  ]
}
```

参照APIはインスタンス単位のResource制限ができないので東京の参照範囲と変更範囲を分ける。Resourceを配列にすれば複数台を列挙できる。SSM接続も許可するなら、SSMのStartSession側にも対象インスタンスを追加する。使用document、データチャネル、自分のセッション終了/再開は別の必要権限。SSM AgentのEC2ロールと、操作側ロールを混同しない。

StopInstancesは再起動可能な停止、TerminateInstancesはインスタンスの削除。「終了」という依頼はどちらかを確定する。追試終了の許可前には、操作権限があっても本戦EC2を停止/削除しない。

## 短期認証情報の取得と更新

取得方法を区別する。
- 手動でAssumeRoleし、AccessKeyId/SecretAccessKey/SessionTokenをcredentialsへ保存: 有効期間内は使えるが、保存した値は自動更新されない。
- 明示的なAssumeRole: 応答をプロセス内で受け取り、限定ロールのキーで後続コマンドを実行できる。応答のCredentials全体を標準出力やログに出さない。
- ロール用プロファイル: CLIが認証元からAssumeRoleし、ロールキーをキャッシュする。更新が必要な時は、次のコマンド実行で再取得する。常駐タイマーではない。

ロール用プロファイルの設定例（説明用。実際の設定と区別して検証する）:
```ini
[profile cc4-operator]
role_arn = arn:aws:iam::123456789012:role/PracticeOperator
source_profile = cc4-practice
region = ap-northeast-1
```
ログイン元はcc4-practice、操作用はcc4-operatorと別名にする。ログイン元プロファイルをロール設定で上書きしない。
```sh
aws sts get-caller-identity --profile cc4-operator --region ap-northeast-1
```
ARNが意図したassumed-roleになったことを確認してから操作する。別profileや環境変数の認証情報が残る場合は優先順位を確認する。

| 保存先 | 内容と役割 |
| --- | --- |
| ~/.aws/config | profile、login_session、role_arn、source_profile等。aws login初回設定/変更では更新されるが、毎回のロール更新で書き換えるものではない |
| ~/.aws/credentials | 手動保存したキー等。ロール用profileによる自動取得では書き換えない |
| ~/.aws/login/cache/ | aws loginの短期認証情報と更新用メタデータ。CLIが必要時に更新 |
| ~/.aws/cli/cache/ | ロール用profileで取得したAssumeRoleの認証情報・期限。CLIが更新 |
| プロセス内のみ | 明示的なAssumeRoleの応答を一時的に使った場合。必ずcli/cacheに保存されるわけではない |

aws loginは最大12時間のログイン期間内で必要時にキーを更新する。期限が来たら人間が再度aws loginする。STS AssumeRoleは既定1時間で、ロール設定と発行方法により期間が異なる。ロールから別ロールへの切り替えは通常最大1時間。認証元が期限切れならロールキーも再取得できない。既に取得したロールキーの期限とログイン期限は別であり、ログイン期限を操作全体の即時失効時刻とはみなさない。

Identity Centerのaws sso loginは別の方式。SSOの期限・SSOキャッシュの話をaws loginの最大12時間へ混ぜない。認証元キー、ログインキャッシュ、ロールキーはすべて資格情報として扱い、Gitへ入れず、内容を一括表示しない。

## ログイン期限切れからの復旧

2026-10-10 JSTの練習で、次の一周を確認した。経過時間はユーザー報告に基づき、正確な失効境界を秒単位で測定したものではない。

| 条件 | 確認結果 |
| --- | --- |
| ログインから約8〜9時間後 | 認証元のidentity確認と、明示的AssumeRoleによる新しいロールキー取得が成功 |
| ログインから12時間以上経過後 | 明示的AssumeRoleが終了255。認証元のセッション期限切れエラー |
| 人間が同じprofileでaws loginを再実行した後 | 明示的AssumeRoleが終了0。指定ロールのARNと、新しいキーのExpirationを確認 |

期限切れ時のエラー:
```text
Your session has expired. Please reauthenticate using 'aws login'.
```

このエラーなら、IAM権限を増やしたり同じ要求を繰り返したりせず、必要なprofileを伝えて人間の再ログインを待つ。
```sh
aws login --profile cc4-practice --region ap-northeast-1
```
ブラウザでは専用IAMユーザーを選ぶ。人間の完了報告後、認証元identityを必要に応じて確認し、明示的AssumeRoleまたは設定済みの操作用profileでロール取得を確認する。ArnとExpirationだけを出力するなど、キー/トークンを表示せず、依頼されていないEC2の変更を復旧テストに使わない。元の作業を再開する際は対象と現在状態を再確認する。

今回確認したのは明示的AssumeRoleによる再取得と再ログイン後の復旧。ロール用profileの自動再取得、ログイン全体の正確な残り時間、期限直前のキーで操作を継続できる期間は未検証。手動再取得と自動更新を同じ検証結果として報告しない。

## サンドボックスと失敗の切り分け

練習では認証確認時に次で停止した。
```text
Read-only file system: .../.aws/login/cache/...json
```
ログインキーの更新にはキャッシュへの書き込みが必要で、読み取り専用の実行環境では止まる。ネットワークやIAMの拒否ではない。許可された実行権限でキャッシュ更新を可能にして同じ確認を再試行した。IAM権限を増やす解決や、キーをチャットへコピーする回避は行わない。

- ローカル書込エラー: キャッシュ保存先と実行環境の書込権限を確認。
- ログイン期限切れ: 人間の再ログインが必要か確認。
- AssumeRoleのAccessDenied: 認証元の許可、対象ロールの信頼、条件を確認。
- EC2 APIのAccessDenied: 引き受けた主体、対象ARN、ロールの操作許可を確認。
- pending: 起動要求の受付。running確認、SSH到達性、アプリ稼働は別の確認。

同じ失敗を無条件で繰り返さない。原因と人間に必要な操作を絞って報告する。権限不足やログイン切れのままEC2操作をループしない。承認レビューが拒否した場合は、対象操作・理由・残る作業を報告する。

## 確認したことと残る検証

2026-10-10 JSTの練習で、専用IAMユーザーのaws login済み状態から、指定ロールへの明示的AssumeRole、指定EC2のstopped→pending→runningを確認した。人間もAWSコンソールで起動を確認し、その後手動停止したと報告した。

キャッシュ書込制限からの再試行、ログイン期限内の再取得、期限切れの検出、人間の再ログイン後の再取得は確認済み。一方、ロール用profileの自動再取得、CodexによるStopInstances、対象外・未許可操作の拒否、aws login由来認証とMFA強制条件の組み合わせは未検証。これらの確認のために依頼されていない操作は実行しない。本戦対象のARNは当日確認して非公開記録へ残す。

## 公式資料

- [aws loginの認証・期限・キャッシュ](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html)
- [CLIのAssumeRole・信頼・キャッシュ](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-role.html)
- [AssumeRoleの有効期間](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)
- [SignInLocalDevelopmentAccess](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/SignInLocalDevelopmentAccess.html)
- [自己MFA管理](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples_aws_my-sec-creds-self-manage-mfa-only.html)
- [自己パスワード変更](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_enable-user-change.html)
- [EC2ポリシー例](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ExamplePolicies_EC2.html)

調査時点の仕様。競技前にCLIバージョンと公式仕様・当日制約を再確認する。
