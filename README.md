# PayPayフリマ受取連絡催促スクリプト

PayPayフリマの取引で配達完了後に受取連絡がされていない場合に、自動でメッセージを送信するスクリプトです。

## 機能

- ヤマト運輸の配送状況を自動チェック
- 配達完了かつ受取連絡未完了の取引に対して催促メッセージを自動送信
- ログ出力による実行状況の記録

## 必要な環境

- Python 3.7以上
- Playwright
- dotenv

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 環境変数の設定

`.env`ファイルを作成し、以下を設定：

```env
USER_DATA_DIR=/path/to/chrome/user/data
PROFILE_DIR=Default
```

**USER_DATA_DIRの確認方法：**
- Chrome: `chrome://version/` で「プロフィール パス」を確認
- 例: `/home/username/.config/google-chrome` (Linux)
- 例: `/Users/username/Library/Application Support/Google/Chrome` (Mac)
- 例: `C:\Users\username\AppData\Local\Google\Chrome\User Data` (Windows)

### 3. 初回認証

```bash
python saisoku.py auth
```

ブラウザが開くので、PayPayフリマ（Yahoo!）にログインしてください。

## 使用方法

### 手動実行

```bash
python saisoku.py "取引URL"
```

### cron設定

#### 毎日午前9時に実行する例：

```bash
crontab -e
```

以下を追加：

```cron
0 9 * * * cd /path/to/script && python saisoku.py "取引URL" >> cron.log 2>&1
```

#### 複数のURLを処理する場合：

`urls.txt`ファイルを作成し、1行に1つずつURLを記載：

```
https://paypayfleamarket.yahoo.co.jp/item/取引ID1
https://paypayfleamarket.yahoo.co.jp/item/取引ID2
```

`run_batch.sh`スクリプトを作成：

```bash
#!/bin/bash
cd /path/to/script
while IFS= read -r url; do
    python saisoku.py "$url"
    sleep 10  # 10秒間隔で実行
done < urls.txt
```

実行権限を付与：

```bash
chmod +x run_batch.sh
```

cron設定：

```cron
0 9 * * * /path/to/script/run_batch.sh >> /path/to/script/batch.log 2>&1
```

## cron設定時の注意点

### 1. 絶対パスを使用

```cron
# ❌ 相対パス（動作しない可能性）
0 9 * * * python saisoku.py "URL"

# ✅ 絶対パス
0 9 * * * cd /home/username/saisoku && /usr/bin/python3 saisoku.py "URL"
```

### 2. 環境変数の設定

cronは最小限の環境変数しか持たないため、必要に応じてPATHを設定：

```cron
PATH=/usr/local/bin:/usr/bin:/bin
0 9 * * * cd /path/to/script && python saisoku.py "URL"
```

### 3. ログローテーション

ログファイルが肥大化しないよう、定期的にローテーションを設定：

```bash
# logrotate設定例 (/etc/logrotate.d/saisoku)
/path/to/script/saisoku.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

### 4. 実行頻度の調整

PayPayフリマの利用規約に配慮し、適切な頻度で実行してください：

```cron
# 毎日1回
0 9 * * * /path/to/script/run.sh

# 週3回（月水金）
0 9 * * 1,3,5 /path/to/script/run.sh

# 毎時実行（頻度が高すぎる可能性があります）
0 * * * * /path/to/script/run.sh
```

## トラブルシューティング

### よくある問題

1. **認証エラー**
   - `python saisoku.py auth`で再認証
   - プロファイルパスが正しいか確認

2. **Playwright関連エラー**
   ```bash
   playwright install chromium
   ```

3. **cron実行時のエラー**
   - ログファイル（`saisoku.log`、`cron.log`）を確認
   - 絶対パスを使用しているか確認
   - 環境変数が正しく設定されているか確認

4. **権限エラー**
   ```bash
   chmod +x saisoku.py
   chmod +x run_batch.sh
   ```

### デバッグ用のcron設定

詳細なログを出力：

```cron
0 9 * * * cd /path/to/script && /usr/bin/python3 -u saisoku.py "URL" >> debug.log 2>&1
```

## セキュリティ上の注意

- ブラウザプロファイルには認証情報が保存されるため、適切なアクセス権限を設定
- スクリプトファイルと`.env`ファイルの権限を制限（`chmod 600`など）
- 定期的にログをチェックし、異常な動作がないか確認

## ログファイル

- `saisoku.log`: スクリプトの実行ログ
- `cron.log`: cron実行時のシステムログ
- `batch.log`: バッチ実行時のログ

これらのファイルを定期的に確認し、正常に動作しているかチェックしてください。
