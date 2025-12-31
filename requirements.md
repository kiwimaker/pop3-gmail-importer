# POP3 to Gmail Importer 要件定義書

## 1. プロジェクト概要

### 1.1 目的
POP3サーバーから受信したメールを、Gmail API経由でGmailアカウントに直接取り込むPythonプログラムを開発する。複数のPOP3アカウントから複数のGmailアカウントへのメール取り込みを1つのプログラムで管理する。

### 1.2 対象ユーザー
- 複数のメールアカウントをGmailで一元管理したいユーザー
- POP3のみ対応のメールサービスをGmailで受信したいユーザー
- メールインポート時のSPF/DKIM/DMARC問題を回避したいユーザー

### 1.3 v3.0での主要変更点

**v2.3（SMTP方式）からの変更理由**:
- Yahoo Japan等のSMTPサーバーがFrom検証を要求し、ヘッダー書き換えが不可能
- SPF/DKIM/DMARC検証失敗による受信拒否・スパム分類リスク
- SMTP経由では根本的な認証問題を解決できない

**v3.0（Gmail API直接取り込み方式）の利点**:
- ✅ **認証問題を完全回避**: SMTP経由ではないため、SPF/DKIM/DMARC問題が発生しない
- ✅ **元のメール情報を完全保持**: 送信者、件名、本文、添付ファイルをそのまま保存
- ✅ **Gmail標準機能との統合**: `messages.import`により、スパムフィルタ・受信トレイ分類が正常動作
- ✅ **確実な到達**: Gmail APIでの取り込みなので、SMTP時の受信拒否リスクを回避

## 2. 機能要件

### 2.1 メール受信機能（POP3）
- **プロトコル**: POP3
- **機能**:
  - POP3サーバーに接続し、受信メールを取得
  - SSL/TLS接続に対応（ポート995推奨）
  - 認証情報は環境変数（.envファイル）から読み込み
  - UIDL（Unique ID Listing）による重複防止

### 2.2 Gmail API取り込み機能

#### 2.2.1 取り込み方式
- **API**: Gmail API v1
- **エンドポイント**: `users.messages.import`
- **認証方式**: OAuth 2.0（デスクトップアプリ）
- **取り込み方法**: 元のメール（RFC 822形式）をGmailの通常受信処理を経由して取り込み
  - 送信者情報（From）完全保持
  - 件名（Subject）完全保持
  - 本文（Body）完全保持
  - 添付ファイル完全保持
  - メールヘッダー（Date, Message-ID等）完全保持
  - Gmailのスパムフィルタ、受信トレイ分類が正常に動作
  - `internalDateSource=dateHeader`でメールの元の日付を保持
  - **labelIds指定の重要性**:
    - `labelIds=['INBOX', 'UNREAD']`を明示的に指定
    - 指定なしの場合、メールがアーカイブ済み・既読として取り込まれる
    - 'INBOX': 受信トレイに配置（アーカイブ回避）
    - 'UNREAD': 未読状態で配置（既読回避）

#### 2.2.2 OAuth 2.0認証フロー
- **初回認証**:
  1. Google Cloud Consoleで作成した`credentials.json`を読み込み
  2. ブラウザが自動起動し、Googleアカウントでログイン
  3. アクセス許可を承認（スコープ: `https://www.googleapis.com/auth/gmail.insert`）
  4. 認証トークンが`token_accountN.json`として保存される

- **2回目以降**:
  1. `token_accountN.json`から自動ログイン
  2. トークン期限切れ時は自動更新
  3. ブラウザ操作は不要

#### 2.2.3 複数Gmail宛先対応
- **設定単位**: POP3アカウントごとに取り込み先Gmailを指定
- **トークン管理**: 取り込み先Gmailアカウントごとに個別のトークンファイル
- **例**:
  ```
  Account 1 (POP3: user1@yahoo.co.jp)   → Gmail A (ohno.waseda@gmail.com)
  Account 2 (POP3: user2@example.com)   → Gmail B (other@gmail.com)
  Account 3 (POP3: user3@example.com)   → Gmail A (ohno.waseda@gmail.com)
  ```
  - Account 1とAccount 3は同じGmail宛先なので、**同じトークンファイルパスを指定**
    ```bash
    ACCOUNT1_GMAIL_TOKEN_FILE=tokens/token_gmail_a.json
    ACCOUNT3_GMAIL_TOKEN_FILE=tokens/token_gmail_a.json  # 同じファイルパス
    ```

#### 2.2.4 Gmail側のラベル付け
- **方式**: Gmail標準フィルタ機能を使用
- **設定場所**: Gmail UI（設定 → フィルタとブロック中のアドレス）
- **推奨構成**:
  ```
  Forwarded/
  ├── Forwarded/Yahoo      (Yahoo Japanからの取り込み)
  ├── Forwarded/Example2   (Example2からの取り込み)
  └── Forwarded/Example3   (Example3からの取り込み)
  ```
- **フィルタ例**:
  - 条件: `From: *@yahoo.co.jp`
  - 操作: ラベル「Forwarded/Yahoo」を付ける
- **利点**:
  - プログラム側でラベルAPIを呼ぶ必要がない
  - Gmail UIで柔軟に変更・追加可能
  - 複数条件の組み合わせも可能

### 2.3 バックアップ機能
- **方式**: ローカルファイル保存（v2.3から変更なし）
- **保存形式**: .eml形式（メールクライアントで開ける標準形式）
- **保存先**: `backup/accountN/` ディレクトリ（アカウント別）
- **ファイル名**: `YYYYMMDD_HHMMSS_<Message-IDハッシュ>.eml`
  - Message-IDのSHA256ハッシュを使用（ファイル名の安全性確保）
  - Message-ID不在時: 生メール全体のSHA256ハッシュで代替
  - 送信者名は使わない（特殊文字・パス区切り文字エラー回避）
- **タイミング**: **Gmail API取り込み前に保存**
  - バックアップ失敗時もGmail API挿入は続行（到達優先）
  - バックアップ失敗は警告ログに記録
- **目的**: POP3サーバー削除後もメール内容を復元可能にする
- **自動削除**: 90日以上前のバックアップファイルを自動削除
- **削除タイミング**: アカウント処理の最後に古いファイルをクリーンアップ

### 2.4 重複防止機能（UIDL管理）
- **方式**: UIDL（Unique ID Listing）によるメール一意識別
- **目的**: 以下のシナリオでの重複取り込みを防止
  - プログラムクラッシュ（Gmail API挿入成功後、POP3削除前）
  - ネットワーク切断（削除コマンド送信前、またはQUIT前）
  - デバッグモード（削除しない設定）での重複実行
- **保存場所**: `state/accountN_uidl.jsonl`
  - アカウント別にUIDL状態を管理
  - JSONL形式（1行1レコード）
- **保存内容**:
  ```json
  {
    "uidl": "メール一意ID",
    "timestamp": "2025-12-31T12:34:56",
    "gmail_target": "ohno.waseda@gmail.com",
    "backup_file": "backup/account1/20251231_123456_abc123def456.eml"
  }
  ```
- **処理フロー**:
  1. POP3接続後、UIDLコマンドでメール一覧取得
  2. ローカル状態ファイルと照合し、未処理メールのみ取得
  3. Gmail API挿入成功後、即座にUIDLを状態ファイルに記録（削除前）
  4. その後、サーバーから削除（本番モード時）
  5. POP3 QUITコマンドで削除を確定
- **重要な仕様**:
  - POP3 DELEコマンドはQUIT時に初めて実行される
  - 接続切断時はDELEマークが無効化される
  - UIDL記録はGmail挿入成功直後に行い、削除失敗時も重複を防止
- **状態ファイルクリーンアップ**:
  - 90日以上前のUIDLレコードを定期削除（バックアップ保持期間と同期）
- **デバッグモード時の挙動**:
  - 削除は行わないが、UIDLは記録する
  - **直近5件の定義**: メールのDateヘッダーで降順ソート、最新5件を処理
  - 古いメール（6件目以降）は自動スキップ
  - **実装詳細**:
    - POP3 TOPコマンドで各メールの先頭20行を取得（Dateヘッダー取得用）
    - 本文全体は取得せず、効率的にソート
    - Date取得失敗時は現在時刻で代替

### 2.5 実行方式
- **方式**: 常駐プログラム（デーモン）
- **動作**: プログラム内で無限ループし、指定間隔ごとにメール取り込み処理を実行
- **想定環境**: ホスティングサーバー、VPS、またはローカルPC
- **処理間隔**: 300秒（5分）デフォルト、環境変数で変更可能

### 2.6 複数アカウント対応
- **方式**: 環境変数での番号付け管理
- **アカウント数**: `ACCOUNT_COUNT` で指定（最大5）
- **命名規則**: `ACCOUNT1_`, `ACCOUNT2_`, `ACCOUNT3_` のように番号プレフィックス
- **処理方法**: 各アカウントを順番に処理（並列ではなく直列）
- **独立性**: 各アカウントは独立してバックアップ・削除・Gmail宛先設定を持つ
- **有効/無効切り替え**: `ACCOUNTN_ENABLED` で個別制御
  - `true`: アカウント有効（処理対象）
  - `false`: アカウント無効（スキップ）

### 2.7 設定管理
- **形式**: 環境変数（.envファイル）
- **起動時検証**:
  - 必須項目の存在確認
  - 設定値の型チェック
  - 設定エラー時は詳細メッセージ表示後、起動中止

#### 2.7.1 共通設定項目
```bash
ACCOUNT_COUNT=5                      # アカウント数（1-5）
CHECK_INTERVAL=300                   # チェック間隔（秒）
MAX_EMAILS_PER_LOOP=100              # 1ループあたり最大処理件数
LOG_LEVEL=INFO                       # ログレベル
LOG_FILE=logs/pop3_gmail_importer.log    # ログファイルパス
LOG_MAX_BYTES=10485760               # ログファイル最大サイズ（10MB）
LOG_BACKUP_COUNT=5                   # ログローテーション保持数
```

#### 2.7.2 アカウント別設定項目（番号付きプレフィックス）

**基本設定**:
```bash
ACCOUNT1_ENABLED=true                # アカウント有効/無効
```

**POP3設定**（v2.3から変更なし）:
```bash
ACCOUNT1_POP3_HOST=pop.mail.yahoo.co.jp
ACCOUNT1_POP3_PORT=995
ACCOUNT1_POP3_USE_SSL=true
ACCOUNT1_POP3_VERIFY_CERT=true
ACCOUNT1_POP3_USERNAME=user@yahoo.co.jp
ACCOUNT1_POP3_PASSWORD=your_password_here
```

**Gmail API設定**（新規）:
```bash
ACCOUNT1_GMAIL_CREDENTIALS_FILE=credentials.json           # OAuth認証情報
ACCOUNT1_GMAIL_TOKEN_FILE=tokens/token_account1.json       # トークン保存先
ACCOUNT1_GMAIL_TARGET_EMAIL=ohno.waseda@gmail.com          # 取り込み先Gmail
```

**削除設定**（v2.3から変更なし）:
```bash
ACCOUNT1_DELETE_AFTER_FORWARD=false  # デバッグモード: false, 本番: true
```

**削除設定の詳細**:
- `false` (デバッグモード):
  - POP3サーバーからメール削除しない
  - 直近5件のみ処理（重複防止のためUIDL記録）
  - テスト・開発用
- `true` (本番モード):
  - Gmail取り込み成功後、POP3サーバーから削除
  - 全メール処理（MAX_EMAILS_PER_LOOP上限まで）
  - 運用環境用

**バックアップ設定**（v2.3から変更なし）:
```bash
ACCOUNT1_BACKUP_ENABLED=true
ACCOUNT1_BACKUP_DIR=backup/account1
ACCOUNT1_BACKUP_RETENTION_DAYS=90
```

**v2.3から削除された設定**:
- ~~`ACCOUNT1_SMTP_HOST`~~ （不要）
- ~~`ACCOUNT1_SMTP_PORT`~~ （不要）
- ~~`ACCOUNT1_SMTP_USE_STARTTLS`~~ （不要）
- ~~`ACCOUNT1_SMTP_USE_SSL`~~ （不要）
- ~~`ACCOUNT1_SMTP_VERIFY_CERT`~~ （不要）
- ~~`ACCOUNT1_SMTP_USERNAME`~~ （不要）
- ~~`ACCOUNT1_SMTP_PASSWORD`~~ （不要）
- ~~`ACCOUNT1_FORWARD_TO`~~ （`GMAIL_TARGET_EMAIL`に変更）

### 2.8 プログラム制御
- **起動**: `python main.py` または `start.bat`（Windows）
- **停止**: Ctrl+C（SIGINT）またはSIGTERMで安全停止
  - シグナルハンドラで処理中メール1件の完了を待機し、即座に停止
  - 次のメール処理は開始せず、POP3セッションをクリーンにクローズ
  - クリーンアップ処理（接続クローズ）
  - 停止メッセージをログに記録
- **注1**: 多重起動防止機能なし（UIDL管理により重複インポートは発生しない）
- **注2**: v2.3までのロックファイル（多重起動防止）は削除
  - **理由**: UIDL管理により重複インポートは発生しない
  - ロックファイルの残存により再起動不可になる問題を回避

## 3. 非機能要件

### 3.1 セキュリティ

#### 3.1.1 認証情報の保護
- `.env`ファイル: Gitに含めない（`.gitignore`で除外）
- `credentials.json`: Gitに含めない（OAuth認証情報）
- `tokens/token_accountN.json`: Gitに含めない（アクセストークン）
- ファイルパーミッション:
  - `.env`: 600（所有者のみ読み書き）
  - `credentials.json`: 600
  - `tokens/*.json`: 600
  - `backup/`: 700（所有者のみアクセス）
  - `state/`: 700

#### 3.1.2 POP3接続のセキュリティ
- **TLS/SSL接続**: デフォルトで有効
- **証明書検証**: デフォルトで有効
  - `ssl.create_default_context()` を使用
  - `POP3_SSL`にSSLContextを渡す
- **証明書検証の無効化**:
  - 環境変数で`ACCOUNTN_POP3_VERIFY_CERT=false`で無効化可能
  - 開発環境・自己署名証明書用
  - 警告ログを出力

#### 3.1.3 Gmail API認証のセキュリティ
- **OAuth 2.0スコープの最小化**:
  ```python
  SCOPES = ['https://www.googleapis.com/auth/gmail.insert']
  ```
  - 読み取り権限なし（挿入のみ）
  - 削除権限なし
  - 送信権限なし
- **トークンリフレッシュ**: 自動更新（`google-auth-oauthlib`が自動処理）
- **認証情報の暗号化**: OSのキーチェーンには保存しない（ファイルベース）

#### 3.1.4 ログ出力の機密情報マスキング
- パスワード: `***`で表示
- メールアドレス: 部分マスキング（`user***@example.com`）
- メール本文: ログ出力禁止
- OAuth トークン: ログ出力禁止

### 3.2 信頼性

#### 3.2.1 エラーハンドリング
- ネットワークエラー時のリトライなし（次の5分間隔ループで再試行）
- 接続タイムアウトの設定
- Gmail API取り込み失敗時のログ記録
- 致命的エラー発生時もプログラム継続（次ループで再試行）

#### 3.2.2 重複防止
- **全モード共通**: UIDL状態ファイルで処理済みメールを記録
- **プログラムクラッシュ時**: Gmail取り込み成功直後にUIDL記録（削除前）
- **ネットワーク切断時**: QUIT失敗でもUIDL記録により次回スキップ
- **デバッグモード**: 削除しないが、UIDL記録で重複防止
- **本番モード**: UIDL記録 + POP3削除の二重防御

#### 3.2.3 取り込み成功の定義
1. Gmail API `messages.import()` が成功（HTTP 200 OK）
2. UIDL状態ファイルへの記録成功

**上記2つが成功した時点で「取り込み成功」と見なす**

**バックアップ処理の扱い**:
- バックアップ有効時は取り込み前に保存を試みる
- バックアップ失敗でもGmail API取り込みは続行
- バックアップ失敗は警告ログに記録
- **理由**: バックアップ失敗で再処理すると重複取り込みが発生

**取り込み失敗の扱い**:
- Gmail API取り込み失敗時はUIDL記録せず、次ループで再試行
- UIDL記録失敗時も取り込み失敗として扱い、次ループで再試行

#### 3.2.4 ログファイル
- ローテーション: 10MB/ファイル、5世代保持
- フォーマット: `YYYY-MM-DD HH:MM:SS - LEVEL - Message`

### 3.3 パフォーマンス
- **メモリ効率**: 大容量添付ファイル対応
- **1ループあたり最大処理件数**:
  - デフォルト100件/アカウント
  - `MAX_EMAILS_PER_LOOP`で変更可能
  - 上限到達時はログに記録、次ループで続行

### 3.4 保守性
- PEP 8準拠
- .envファイルによる柔軟な設定変更
- ログ出力による動作状況の可視化

## 4. 技術スタック

### 4.1 プログラミング言語
- Python 3.9以上

### 4.2 主要ライブラリ

**v2.3から継続**:
- `poplib`: POP3クライアント
- `email`: メール解析
- `python-dotenv`: .envファイル読み込み
- `logging`: ログ出力

**v3.0で新規追加**:
- `google-auth==2.27.0`: Google認証ライブラリ
- `google-auth-oauthlib==1.2.0`: OAuth 2.0フロー
- `google-auth-httplib2==0.2.0`: HTTP認証
- `google-api-python-client==2.115.0`: Gmail API クライアント

**v2.3から削除**:
- ~~`smtplib`~~: SMTP不要

## 5. システム構成

### 5.1 ディレクトリ構成
```
pop3_gmail_importer/
├── .env.example             # 環境変数テンプレート
├── .gitignore               # Git除外設定
├── main.py                  # メインプログラム
├── test_connection.py       # 接続テストプログラム
├── requirements.txt         # Python依存関係
├── start.bat                # Windows起動スクリプト
├── README.md                # 使用方法
├── credentials.json         # OAuth認証情報（ユーザーが配置）
├── tokens/                  # アクセストークン（自動生成）
│   ├── token_account1.json
│   ├── token_account2.json
│   └── ...
├── state/                   # UIDL状態管理（自動生成）
│   ├── account1_uidl.jsonl
│   ├── account2_uidl.jsonl
│   └── ...
├── backup/                  # メールバックアップ（自動生成）
│   ├── account1/
│   ├── account2/
│   └── ...
├── logs/                    # ログファイル（自動生成）
│   └── pop3_gmail_importer.log
└── venv/                    # Python仮想環境（自動生成）
```

**`.gitignore`に追加**:
```
.env
credentials.json
tokens/
state/
backup/
logs/
venv/
.lock
```

### 5.2 接続テストプログラム（test_connection.py）

**機能**:
1. .envファイルから全アカウント設定を読み込み
2. 各アカウント（`ENABLED=true`のみ）について:
   - **POP3接続テスト**:
     - サーバー接続確認
     - SSL/TLS接続確認
     - 認証確認
     - UIDL対応確認
     - メッセージ件数取得
   - **Gmail API接続テスト**:
     - `credentials.json`存在確認
     - OAuth認証フロー実行（初回のみブラウザ起動）
     - トークンファイル生成確認
     - 認証成功確認（トークンの有効性検証）
3. テスト結果を色付きで表示:
   - ✓ 成功（緑）
   - ✗ 失敗（赤）
   - 詳細なエラーメッセージ

**実行方法**:
```bash
python test_connection.py
```

**出力例**:
```
Testing Account 1...
  [✓] POP3 Connection: OK
  [✓] POP3 Authentication: OK
  [✓] POP3 UIDL Support: SUPPORTED
  [✓] Gmail API Credentials: Found
  [✓] Gmail API OAuth: Authenticated (ohno.waseda@gmail.com)
  [✓] Gmail API Connection: OK

Testing Account 2...
  [✗] POP3 Connection: Timeout
  ...

Summary: 1/2 accounts passed
```

### 5.3 Windows起動スクリプト（start.bat）

**機能**:
1. Python 3.9以上の確認
2. venv仮想環境作成（未存在時）
3. 仮想環境アクティベート
4. `pip install -r requirements.txt` 実行
5. `.env`ファイル存在確認
6. `credentials.json`存在確認（Gmail API用）
7. `main.py`実行

**注**: バッチファイル内は全て英語コメント（文字化け防止）

### 5.4 環境変数例（.env.example）

```bash
# ========================================
# Global Settings
# ========================================
ACCOUNT_COUNT=5
# Check interval in seconds (300 = 5 minutes)
CHECK_INTERVAL=300
# Max emails to process per account per loop
MAX_EMAILS_PER_LOOP=100

# Log Settings
LOG_LEVEL=INFO
LOG_FILE=logs/pop3_gmail_importer.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# ========================================
# Account 1 Settings
# ========================================
ACCOUNT1_ENABLED=true

# POP3 Settings
ACCOUNT1_POP3_HOST=pop.mail.yahoo.co.jp
ACCOUNT1_POP3_PORT=995
ACCOUNT1_POP3_USE_SSL=true
# TLS certificate verification (recommended: true)
ACCOUNT1_POP3_VERIFY_CERT=true
ACCOUNT1_POP3_USERNAME=user1@yahoo.co.jp
ACCOUNT1_POP3_PASSWORD=your_password_here

# Gmail API Settings
ACCOUNT1_GMAIL_CREDENTIALS_FILE=credentials.json
ACCOUNT1_GMAIL_TOKEN_FILE=tokens/token_account1.json
ACCOUNT1_GMAIL_TARGET_EMAIL=ohno.waseda@gmail.com

# Deletion Settings
ACCOUNT1_DELETE_AFTER_FORWARD=false

# Backup Settings
ACCOUNT1_BACKUP_ENABLED=true
ACCOUNT1_BACKUP_DIR=backup/account1
ACCOUNT1_BACKUP_RETENTION_DAYS=90

# ========================================
# Account 2 Settings
# ========================================
ACCOUNT2_ENABLED=true

# POP3 Settings
ACCOUNT2_POP3_HOST=pop.example2.com
ACCOUNT2_POP3_PORT=995
ACCOUNT2_POP3_USE_SSL=true
ACCOUNT2_POP3_VERIFY_CERT=true
ACCOUNT2_POP3_USERNAME=user2@example2.com
ACCOUNT2_POP3_PASSWORD=your_password_here

# Gmail API Settings
ACCOUNT2_GMAIL_CREDENTIALS_FILE=credentials.json
ACCOUNT2_GMAIL_TOKEN_FILE=tokens/token_account2.json
ACCOUNT2_GMAIL_TARGET_EMAIL=other@gmail.com

# Deletion Settings
ACCOUNT2_DELETE_AFTER_FORWARD=true

# Backup Settings
ACCOUNT2_BACKUP_ENABLED=true
ACCOUNT2_BACKUP_DIR=backup/account2
ACCOUNT2_BACKUP_RETENTION_DAYS=90

# ========================================
# Account 3 Settings
# ========================================
ACCOUNT3_ENABLED=false

# POP3 Settings
ACCOUNT3_POP3_HOST=pop.example3.com
ACCOUNT3_POP3_PORT=995
ACCOUNT3_POP3_USE_SSL=true
ACCOUNT3_POP3_VERIFY_CERT=true
ACCOUNT3_POP3_USERNAME=user3@example3.com
ACCOUNT3_POP3_PASSWORD=your_password_here

# Gmail API Settings
ACCOUNT3_GMAIL_CREDENTIALS_FILE=credentials.json
ACCOUNT3_GMAIL_TOKEN_FILE=tokens/token_account3.json
ACCOUNT3_GMAIL_TARGET_EMAIL=forward@destination.com

# Deletion Settings
ACCOUNT3_DELETE_AFTER_FORWARD=true

# Backup Settings
ACCOUNT3_BACKUP_ENABLED=true
ACCOUNT3_BACKUP_DIR=backup/account3
ACCOUNT3_BACKUP_RETENTION_DAYS=90

# ========================================
# Account 4 Settings
# ========================================
ACCOUNT4_ENABLED=false

# POP3 Settings
ACCOUNT4_POP3_HOST=pop.example4.com
ACCOUNT4_POP3_PORT=995
ACCOUNT4_POP3_USE_SSL=true
ACCOUNT4_POP3_VERIFY_CERT=true
ACCOUNT4_POP3_USERNAME=user4@example4.com
ACCOUNT4_POP3_PASSWORD=your_password_here

# Gmail API Settings
ACCOUNT4_GMAIL_CREDENTIALS_FILE=credentials.json
ACCOUNT4_GMAIL_TOKEN_FILE=tokens/token_account4.json
ACCOUNT4_GMAIL_TARGET_EMAIL=forward@destination.com

# Deletion Settings
ACCOUNT4_DELETE_AFTER_FORWARD=true

# Backup Settings
ACCOUNT4_BACKUP_ENABLED=true
ACCOUNT4_BACKUP_DIR=backup/account4
ACCOUNT4_BACKUP_RETENTION_DAYS=90

# ========================================
# Account 5 Settings
# ========================================
ACCOUNT5_ENABLED=false

# POP3 Settings
ACCOUNT5_POP3_HOST=pop.example5.com
ACCOUNT5_POP3_PORT=995
ACCOUNT5_POP3_USE_SSL=true
ACCOUNT5_POP3_VERIFY_CERT=true
ACCOUNT5_POP3_USERNAME=user5@example5.com
ACCOUNT5_POP3_PASSWORD=your_password_here

# Gmail API Settings
ACCOUNT5_GMAIL_CREDENTIALS_FILE=credentials.json
ACCOUNT5_GMAIL_TOKEN_FILE=tokens/token_account5.json
ACCOUNT5_GMAIL_TARGET_EMAIL=forward@destination.com

# Deletion Settings
ACCOUNT5_DELETE_AFTER_FORWARD=true

# Backup Settings
ACCOUNT5_BACKUP_ENABLED=true
ACCOUNT5_BACKUP_DIR=backup/account5
ACCOUNT5_BACKUP_RETENTION_DAYS=90
```

## 6. ユースケース

### 6.1 基本フロー

1. **プログラム起動時**:
   - 環境変数（.env）読み込み
   - `ACCOUNT_COUNT`確認
   - 必要なディレクトリ作成（`state/`, `backup/accountN/`, `logs/`, `tokens/`）

2. **無限ループ開始**:
   - **各アカウントを順番に処理**（1から`ACCOUNT_COUNT`まで）:
     - **`ACCOUNTN_ENABLED=false`の場合**: スキップ
     - **`ACCOUNTN_ENABLED=true`の場合**:

       a. **UIDL状態ロード**
       b. **POP3接続**
       c. **UIDL一覧取得**
       d. **未処理メール抽出**
       e. **デバッグモード時**: Date降順ソート、上位5件のみ処理
       f. **最大処理件数制限**: `MAX_EMAILS_PER_LOOP`を超える場合は先頭N件のみ処理
       g. **各メールについて**:
          1. メール本文取得（`RETR`コマンド）
          2. **バックアップ保存**（有効時）
             - 失敗時: 警告ログ記録、処理続行
          3. **Gmail API OAuth認証**
             - トークンファイル読み込み
             - 期限切れ時: 自動更新
             - 初回時: ブラウザで承認
          4. **Gmail API `messages.import()`実行**
             - RFC 822形式メールをbase64url-encodeして送信
             - パラメータ:
               - `internalDateSource=dateHeader`（元の日付を保持）
               - `labelIds=['INBOX', 'UNREAD']`（受信トレイに未読として配置）
             - 成功: HTTP 200 OK
             - 失敗: エラーログ記録、次メールへ
          5. **UIDL状態保存**（Gmail取り込み成功時）
          6. **POP3削除マーク**（本番モード時）
       h. **POP3接続終了**（`QUIT` - 削除確定）
       i. **古いバックアップ削除**（90日以上前）
       j. **古いUIDLレコード削除**（90日以上前）
       k. **処理結果ログ記録**

   - **全アカウント処理完了後**:
     - `CHECK_INTERVAL`秒スリープ
     - ループ先頭へ戻る

### 6.2 エラーハンドリング

- **POP3接続エラー**: エラーログ記録 → 次アカウントへ（次の5分間隔ループで再試行）
- **POP3認証エラー**: エラーログ記録 → 次アカウントへ
- **Gmail API OAuth失敗**: エラーログ記録 → 次アカウントへ（初回は手動認証必要）
- **Gmail API取り込み失敗**: エラーログ記録 → 次メールへ（UIDL記録せず、次ループで再試行）
- **UIDL記録失敗**: エラーログ記録 → 次メールへ
- **予期しないエラー**: エラーログ記録 → クラッシュせずループ継続

**リトライ方針**: エラー発生時は即座にリトライせず、次の定期ループ（5分後）で自動的に再試行される

### 6.3 Gmail側のフィルタ設定（ユーザー操作）

1. Gmail UI → 設定 → フィルタとブロック中のアドレス
2. 新しいフィルタ作成:
   - **From**: `*@yahoo.co.jp`
   - **操作**: ラベル「Forwarded/Yahoo」を付ける
   - **注**: 「一致するスレッドにもフィルタを適用する」にチェック
3. 同様に他のPOP3アカウントもフィルタ設定

**推奨ラベル構成**:
```
Forwarded/
├── Yahoo
├── Example2
└── Example3
```

## 7. Google Cloud Console設定手順

### 7.1 プロジェクト作成

1. https://console.cloud.google.com/ にアクセス
2. 「プロジェクトを作成」をクリック
3. プロジェクト名: `POP3 to Gmail Importer` （任意）
4. 「作成」をクリック

### 7.2 Gmail API有効化

1. 左メニュー → 「APIとサービス」 → 「ライブラリ」
2. 検索ボックスで「Gmail API」を検索
3. 「Gmail API」をクリック
4. 「有効にする」をクリック

### 7.3 OAuth 2.0認証情報作成

1. 左メニュー → 「APIとサービス」 → 「認証情報」
2. 「認証情報を作成」→ 「OAuth クライアント ID」
3. **OAuth同意画面の設定**（初回のみ）:
   - ユーザータイプ: 「外部」を選択 → 「作成」
   - アプリ名: `POP3 to Gmail Importer` （任意）
   - ユーザーサポートメール: 自分のGmail
   - デベロッパーの連絡先情報: 自分のGmail
   - 「保存して次へ」
   - スコープ: 「スコープを追加または削除」→ 手動入力:
     ```
     https://www.googleapis.com/auth/gmail.insert
     ```
   - 「保存して次へ」
   - テストユーザー: 「ユーザーを追加」→ **全ての取り込み先Gmailアドレスを追加**
     ```
     例: ohno.waseda@gmail.com, other@gmail.com など、.envで設定した全Gmail
     ⚠️ 1つでも追加漏れがあると、そのGmailアカウントでOAuth認証時にエラーになります
     ```
   - 「保存して次へ」
4. **OAuth クライアント ID作成**:
   - アプリケーションの種類: 「デスクトップ アプリ」
   - 名前: `POP3 to Gmail Importer Desktop Client` （任意）
   - 「作成」をクリック
5. **認証情報ダウンロード**:
   - 表示されたダイアログで「JSONをダウンロード」
   - ダウンロードしたファイルを`credentials.json`にリネーム
   - プロジェクトルートに配置

### 7.4 セキュリティ注意事項

- **公開範囲**: OAuth同意画面は「外部」で問題なし（自分のみ使用）
- **テストユーザー**: 取り込み先Gmailアドレスを**全て**追加（追加漏れがあると認証エラー）
- **本番公開不要**: 個人利用なのでアプリ公開審査は不要
- **認証情報の保護**: `credentials.json`はGitに含めない

## 8. 今後の拡張可能性

### 8.1 フェーズ2以降の検討事項
- フィルタリング機能（送信者、件名、添付ファイル）
- アカウント並列処理（マルチスレッド/マルチプロセス）
- Web UI での設定管理
- 統計情報ダッシュボード
- Gmail側でのラベル自動付与（Gmail API `labels` リソース使用）

## 9. スケジュール

### 9.1 開発フェーズ
- **フェーズ1**: Google Cloud Console設定、OAuth認証テスト
- **フェーズ2**: Gmail API接続テストプログラム作成
- **フェーズ3**: 基本機能実装（POP3受信、Gmail API挿入、UIDL管理）
- **フェーズ4**: バックアップ、エラーハンドリング、ログ機能
- **フェーズ5**: Windows起動スクリプト、ドキュメント作成
- **フェーズ6**: テスト、デプロイ、運用開始

## 10. 制約事項

### 10.1 技術的制約
- **POP3の制約**: サーバー削除後のメール復元は不可
- **Gmail API制約**:
  - 割り当て制限: プロジェクト単位で管理（個人利用では通常十分）
  - `messages.import()`制限: 秒間250リクエスト（個人利用では問題なし）
  - 大容量添付ファイル: 25MB以上はGmail側で受信制限
  - 詳細: [Gmail API Usage Limits](https://developers.google.com/gmail/api/reference/quota)
- **OAuth 2.0制約**:
  - 初回認証時にブラウザ操作必須
  - サーバーレス環境（ブラウザなし）では初回認証不可
  - 解決策: ローカルPCで初回認証後、トークンファイルをサーバーに転送

### 10.2 運用上の制約
- **デバッグモード**: `DELETE_AFTER_FORWARD=false`時、POP3サーバーにメール残存
- **UIDL安定性**: POP3サーバー移行時にUIDLが変化する可能性
- **トークン有効期限**: 長期間未使用時にトークン期限切れ（手動再認証必要）

### 10.3 v2.3からの移行時の注意
- **SMTP設定削除**: `.env`からSMTP関連設定を全削除
- **credentials.json配置**: Google Cloud Consoleからダウンロード必須
- **初回OAuth認証**: ブラウザでの手動承認が必要（各Gmail宛先ごと）
- **state/互換性**: UIDL形式変更（`forward_to`→`gmail_target`）、既存データは互換

## 11. 承認

| 項目 | 内容 |
|------|------|
| 作成日 | 2025-12-31 |
| 最終更新日 | 2025-12-31 |
| 作成者 | Claude Code |
| バージョン | 3.0 |
| 変更履歴 | v2.0: 専門家レビュー反映（UIDL管理、添付転送、TLS証明書検証、デバッグモード5件制限）<br>v2.1: 専門家2回目レビュー反映（UIDL安定性対策、STARTTLS/SSL分離、転送成功定義修正、最大処理件数制限）<br>v2.2: 優先度高レビュー対応（バックアップタイミング統一、直近5件をDate降順に変更、UIDL変化時の安全弁強化、Message-ID不在時フォールバック）<br>v2.3: 転送方式変更（添付転送→ヘッダー書き換え転送、透過的転送、SPF/DKIM/DMARCリスク明記）<br>**v3.0: Gmail API直接取り込み方式に全面移行（SMTP削除、OAuth 2.0認証、messages.import API、Gmail標準受信処理経由、複数Gmail宛先対応、SPF/DKIM/DMARC問題完全解決、ロックファイル削除）** |
