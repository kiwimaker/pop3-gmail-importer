# POP3 to Gmail Importer v3.0

複数のPOP3アカウントからGmail APIを使用してGmailに直接メールをインポートする、本番環境対応のメールインポートデーモンです。Gmail APIのネイティブインポート機能を使用することで、SPF/DKIM/DMARCの問題を完全に回避します。

## v3.0の新機能

- **Gmail API統合**: `messages.import()` APIを使用した直接メールインポート
- **SMTP問題の解消**: SPF/DKIM/DMARC検証失敗を完全に回避
- **Gmail標準処理**: インポートされたメールはGmailのスパムフィルタと受信トレイ分類を経由
- **OAuth 2.0認証**: 安全なトークンベース認証
- **元のメール保持**: すべてのヘッダー、添付ファイル、メタデータを完全に保持
- **未読・受信トレイ配置**: `labelIds`指定により、メールが未読状態で受信トレイに配置される

## 機能

- **複数アカウント対応**: 最大5つのPOP3アカウントから複数のGmailアカウントへインポート
- **Gmail APIインポート**: `messages.import()`を使用して元のメール日付とヘッダーを保持
- **重複防止**: UIDLベースの追跡により、クラッシュ後も重複インポートを防止
- **自動バックアップ**: 設定可能な保持期間でメールアーカイブをオプション提供
- **安全な接続**: 証明書検証付きのPOP3用完全TLS/SSL対応
- **安全なシャットダウン**: Ctrl+C割り込みをデータ損失なく安全に処理
- **デバッグモード**: テスト用に最新5件のメールのみ処理（削除無効時）
- **クラッシュ回復**: アトミック操作により、停電やクラッシュ時も状態を失わない

## 必要要件

- **Python 3.9以上**
- UIDL対応のPOP3メールアカウント
- メールインポート用の**Gmailアカウント**
- Gmail API有効化済みの**Google Cloudプロジェクト**（無料作成可能）

## クイックスタート

### 1. Google Cloudセットアップ

プログラム実行前に、Gmail APIアクセスをセットアップする必要があります：

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成（または既存を選択）
3. Gmail APIを有効化：
   - 「APIとサービス」→「ライブラリ」に移動
   - 「Gmail API」を検索して有効化
4. OAuth 2.0認証情報を作成：
   - 「APIとサービス」→「認証情報」に移動
   - 「認証情報を作成」→「OAuth クライアント ID」をクリック
   - プロンプトが表示されたらOAuth同意画面を設定：
     - ユーザータイプ: 外部
     - アプリ名: 「POP3 to Gmail Importer」（任意の名前）
     - テストユーザーにGmailアドレスを追加
     - スコープ: `https://www.googleapis.com/auth/gmail.insert`を追加
   - アプリケーションの種類: 「デスクトップアプリ」
   - JSONファイルをダウンロード
5. ダウンロードしたファイルを`credentials.json`にリネーム
6. `credentials.json`をプロジェクトルートディレクトリに配置

### 2. 初期セットアップ

1. このプロジェクトをダウンロードまたはクローン
2. サンプル設定をコピー：
   ```bash
   cp .env.example .env
   ```
3. `.env`ファイルを設定で編集（設定セクションを参照）
4. 依存関係をインストール：
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### 3. 接続テスト

接続テストプログラムを実行：

```bash
python test_connection.py
```

これにより：
- POP3接続をテスト
- OAuth認証を実行（初回実行時にブラウザが開きます）
- 今後の使用のために認証トークンを保存
- Gmail APIアクセスを検証

**重要**: 初回実行時、各Gmailアカウントへのアクセス承認のためにブラウザが開きます。「許可」をクリックしてPOP3 to Gmail Importerにメールインポート権限を付与してください。

### 4. 実行

メールインポーターを開始：

```bash
python main.py
```

プログラムは以下を実行します：
- 5分ごとに新しいメールをチェック（設定変更可能）
- Gmail APIを介して新しいメールをインポート
- ローカルバックアップを保存（有効時）
- すべてのアクティビティを`logs/pop3_gmail_importer.log`に記録

### 5. 停止

`Ctrl+C`を押してプログラムを安全に停止します。インポーターは終了前に現在のメール処理を完了します。

## 設定

`.env`ファイルを編集してメールアカウントを設定します。

### グローバル設定

```bash
ACCOUNT_COUNT=5              # 設定するアカウント数（1-5）
CHECK_INTERVAL=300           # チェック間隔（秒）（300 = 5分）
MAX_EMAILS_PER_LOOP=100      # アカウントごとの1ループあたりの最大処理メール数

# ログ設定
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/pop3_gmail_importer.log
LOG_MAX_BYTES=10485760       # ログファイルあたり10MB
LOG_BACKUP_COUNT=5           # ローテーションログファイルを5つ保持
```

### アカウントごとの設定

各アカウントについて（`ACCOUNT1_`を`ACCOUNT2_`、`ACCOUNT3_`などに置き換え）：

```bash
# このアカウントを有効/無効化
ACCOUNT1_ENABLED=true

# POP3設定（ソースメールアカウント）
ACCOUNT1_POP3_HOST=pop.example.com
ACCOUNT1_POP3_PORT=995                # 通常SSL/TLSは995
ACCOUNT1_POP3_USE_SSL=true
ACCOUNT1_POP3_VERIFY_CERT=true        # 推奨: true
ACCOUNT1_POP3_USERNAME=user@example.com
ACCOUNT1_POP3_PASSWORD=your_password_here

# Gmail API設定（宛先Gmailアカウント）
ACCOUNT1_GMAIL_CREDENTIALS_FILE=credentials.json           # OAuth認証情報
ACCOUNT1_GMAIL_TOKEN_FILE=tokens/token_account1.json       # トークン保存先
ACCOUNT1_GMAIL_TARGET_EMAIL=your-gmail@gmail.com           # インポート先

# 削除設定
ACCOUNT1_DELETE_AFTER_FORWARD=false   # デバッグ: false, 本番: true

# バックアップ設定
ACCOUNT1_BACKUP_ENABLED=true
ACCOUNT1_BACKUP_DIR=backup/account1
ACCOUNT1_BACKUP_RETENTION_DAYS=90
```

### 重要な注意事項

- **credentials.json**: 全アカウントで共有（アプリケーション全体で1ファイル）
- **トークンファイル**: 宛先Gmailアカウントごとに1つ
  - 例: Account 1とAccount 3が両方とも`your-gmail@gmail.com`にインポートする場合、同じトークンファイルを共有できます：
    ```bash
    ACCOUNT1_GMAIL_TOKEN_FILE=tokens/token_gmail_a.json
    ACCOUNT3_GMAIL_TOKEN_FILE=tokens/token_gmail_a.json
    ```
- **DELETE_AFTER_FORWARD=false**: デバッグモード - 最新5件のメールのみ処理、サーバーから削除しない
- **DELETE_AFTER_FORWARD=true**: 本番モード - インポート成功後、POP3サーバーからメールを削除

## Gmailフィルタ（オプション）

Gmailでインポートされたメールに自動的にラベルを付けるには：

1. Gmail → 設定 → フィルタとブロック中のアドレス に移動
2. 新しいフィルタを作成：
   - **From**: `*@example.com`（またはソースドメイン）
   - **操作**: ラベル「Forwarded/Example」を適用
   - 「一致する会話にもフィルタを適用する」にチェック
3. 他のPOP3アカウントについても繰り返し

推奨ラベル構造：
```
Forwarded/
├── Example1
├── Example2
└── Example3
```

## 動作の仕組み

1. **POP3取得**: POP3サーバーに接続して新しいメールを取得
2. **UIDL追跡**: UIDL状態をチェックして既に処理済みのメールをスキップ
3. **ローカルバックアップ**: `.eml`ファイルとしてメールを保存（有効時）
4. **Gmail APIインポート**: 元のRFC 822メールで`messages.import()`を呼び出し
   - **labelIds指定**: `['INBOX', 'UNREAD']`で受信トレイに未読として配置
   - labelIds指定なしの場合、メールはアーカイブ済み・既読として取り込まれます
5. **UIDL記録**: インポート成功直後にメールを処理済みとしてマーク
6. **サーバー削除**: POP3サーバーから削除（本番モードのみ）
7. **クリーンアップ**: 古いバックアップとUIDLレコードを削除（デフォルト90日）

## OAuth認証の詳細

### 初回実行
- ブラウザが自動的に開きます
- Gmailアカウントでサインイン
- メールインポート権限を付与
- トークンが`tokens/token_accountN.json`に保存

### 2回目以降の実行
- トークンが自動的にロード
- 期限切れ時に自動更新
- ブラウザ操作は不要

### 複数のGmail宛先
複数のGmailアカウントにインポートする場合、一意の宛先メールごとにOAuthフローが1回実行されます。

## トラブルシューティング

### 「credentials.json not found」
- Google Cloud ConsoleからOAuth認証情報をダウンロード
- `credentials.json`にリネーム
- プロジェクトルートディレクトリに配置

### 「OAuth authentication failed」
- GmailアドレスがGoogle Cloud Consoleのテストユーザーに追加されているか確認
- OAuthスコープが正しいか確認: `https://www.googleapis.com/auth/gmail.insert`
- トークンファイルを削除して再認証を試行

### 「Gmail API error: 403」
- Gmailアドレスがテストユーザーリストにありません
- Google Cloud Console → OAuth同意画面 → テストユーザー に追加

### 「POP3 connection failed」
- ホスト、ポート、ユーザー名、パスワードを確認
- メールプロバイダーでPOP3が有効になっているか確認
- 一部のプロバイダーは通常のパスワードの代わりに「アプリパスワード」が必要

## セキュリティ

- OAuthトークンは`600`権限で保存（所有者の読み取り/書き込みのみ）
- パスワードはログに保存されません（`***`でマスク）
- メールアドレスはログで部分的にマスク（`u***@example.com`）
- `.gitignore`がすべての機密ファイルを除外するよう設定：
  - `.env`
  - `credentials.json`
  - `tokens/`
  - `state/`
  - `backup/`

## ログ

ログは`logs/pop3_gmail_importer.log`に自動ローテーションで保存：
- 最大サイズ: ファイルあたり10MB
- 保持: ローテーションファイル5つ
- フォーマット: `YYYY-MM-DD HH:MM:SS - LEVEL - Message`

## ファイル構造

```
pop3_gmail_importer/
├── .env                     # 設定ファイル（gitに含まれない）
├── .env.example             # 設定テンプレート
├── credentials.json         # OAuth認証情報（gitに含まれない）
├── main.py                  # メインプログラム
├── test_connection.py       # 接続テスター
├── requirements.txt         # Python依存関係
├── README.md                # このファイル（日本語）
├── README_EN.md             # 英語版README
├── tokens/                  # OAuthトークン（gitに含まれない）
│   ├── token_account1.json
│   └── token_account2.json
├── state/                   # UIDL状態ファイル（gitに含まれない）
│   ├── account1_uidl.jsonl
│   └── account2_uidl.jsonl
├── backup/                  # メールバックアップ（gitに含まれない）
│   ├── account1/
│   └── account2/
└── logs/                    # ログファイル（gitに含まれない）
    └── pop3_gmail_importer.log
```

## ライセンス

このプロジェクトは個人使用向けに「現状のまま」提供されます。

## サポート

問題や質問については、以下を確認してください：
1. このREADME
2. 詳細仕様については`requirements.md`
3. `logs/pop3_gmail_importer.log`のログファイル
