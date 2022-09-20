## 設定ファイル(webhook.json)の場所
環境変数「CONFIG_PATH」から場所を取得する

## webhook.jsonの書式
```json
[
  {
    "repository": "sales",
    "branch": "dev/ryan",
    "token": "FoRQPztwwUnU1Qds5GJJg50Jz8uqntVWH8Uo67Hsyu8cASn9Qh",
    "shell": "git -C /workspace/eb_sales pull"
  },
  {
    
  }
]
```

## 各項目の意味
| 属性         | 説明                           |
|:-----------|:-----------------------------|
| repository | レポジトリ名称                      |
| branch     | ブランチ名称                       |
| token      | SecretCode現在Githubしかサポートしません |
| shell      | Webhookからのリクエスト来た後実行する処理     |
