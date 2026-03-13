LAN 檔案分享系統模組化設計

場景：使用者在同一個局域網 (LAN) 內，希望有一個簡單的檔案分享網站。從登入頁 (Landing Page) 可以選擇「註冊 (Sign Up)」或「登入 (Sign In)」，登入後跳轉到檔案分享頁面。使用者可以上傳檔案（限制 50 MB）、下載檔案、刪除自己上傳的檔案，並可看到檔案列表及每個檔案的基本資訊。此系統應採用輕量級資料庫（如 SQLite），並以模組化方式設計，方便後續擴充與維護。

1. 架構總覽

整體採 MVC（Model–View–Controller）風格，可拆分為前端介面、後端服務、資料庫與檔案儲存四大層。

前端介面 (View)：提供註冊、登入、檔案分享頁等 HTML/JS/CSS 頁面。採用模板系統（如 Flask 的 Jinja2）讓頁面結構與資料分離。

後端應用 (Controller)：負責處理路由、使用者驗證、檔案上傳/下載/刪除等邏輯，並調用資料庫和檔案服務模組。

資料庫 (Model)：使用 SQLite 儲存使用者資料與檔案元資料。資料表可包括 users 和 files 兩張表。

檔案儲存：檔案實際存放於伺服器的 uploads/ 目錄，並搭配檔案服務模組完成儲存與讀取。Flask 官方建議在處理檔案上傳時使用 secure_filename() 函式來安全化檔名，避免使用者透過特殊路徑覆寫其他檔案。

1.1 系統流程

未登入者訪問根網址 (/) 時顯示 Landing Page。頁面包含「註冊」與「登入」按鈕。

使用者可選擇：

註冊：跳轉到 /register 進行帳號建立，後端確認使用者名稱未存在後將資訊（含雜湊後密碼）寫入資料庫。

登入：跳轉到 /login，輸入帳號密碼後，後端驗證密碼雜湊，成功則建立 session 並導向檔案分享頁 /files。

已登入者訪問 /files 時看到檔案分享頁：

頁面上方顯示目前登入者名稱與「登出」按鈕。

50 MB 上傳限制提示；提供檔案選擇按鈕與上傳按鈕。

下方顯示檔案列表表格：檔名、檔案大小、上傳者、上傳時間及操作按鈕（下載、刪除）。

使用者點擊「下載」將透過後端 send_from_directory() 函式將檔案回傳。

點擊「刪除」時先檢查使用者是否為檔案擁有者，確認後刪除磁碟上檔案以及資料庫紀錄。

使用者按下「登出」，後端清除 session 並返回 Landing Page。

2. 模組化拆分

以下以 Python/Flask 範例說明，其他後端語言（例如 Node.js + Express）也可遵循相同模組概念。

2.1 專案結構範例
lan_file_sharing/
├── app.py              # 應用啟動與路由註冊
├── config.py           # 系統設定（秘密金鑰、上傳目錄、檔案大小限制）
├── db.py               # 資料庫連線與操作函式
├── auth.py             # 使用者註冊/登入/登出邏輯
├── file_service.py     # 檔案上傳、下載、刪除及檔案類型檢查
├── models.py           # ORM 或 SQL 定義（使用者與檔案模型）
├── templates/          # Jinja2 模板：base.html、login.html、register.html、files.html 等
├── static/             # 靜態資源：CSS/JS
└── uploads/            # 使用者上傳的檔案（依照實際部署可採用絕對路徑）
2.2 設定與常數（config.py）

SECRET_KEY：用於 Flask session 的秘密金鑰。

UPLOAD_FOLDER：檔案儲存路徑，例如 uploads/。

MAX_CONTENT_LENGTH：限制 HTTP 請求體大小。Flask 提供 MAX_CONTENT_LENGTH 參數，可限制上傳檔案的最大尺寸，若超過則會拋出 RequestEntityTooLarge 例外。本系統設定為 50 * 1024 * 1024。

ALLOWED_EXTENSIONS：允許上傳的檔案副檔名集合，例如 {"txt", "pdf", "png", "jpg", "jpeg", "gif"}。限制副檔名可避免 XSS 或惡意腳本上傳。

2.3 資料庫模組（db.py）

此模組負責：

建立資料庫連線：透過 sqlite3.connect() 取得連線並設定 row_factory 方便以字典形式存取欄位。

初始化資料表：應於應用啟動時呼叫，建立兩張表：

users：欄位包括 id (INTEGER PRIMARY KEY AUTOINCREMENT), username (TEXT UNIQUE), password_hash (TEXT), email (TEXT), created_at (TIMESTAMP)。

files：欄位包括 id, filename, filepath, size, uploaded_by (INTEGER FOREIGN KEY -> users.id), uploaded_at (TIMESTAMP)。

通用查詢/執行函式：封裝 execute 與 commit，用於其他模組存取資料庫。

資料表範例定義可參考 [Medium 的 Flask + SQLite 範例文章]，其示範如何建立 user 資料表並在應用啟動時呼叫 create_tables()。

2.4 認證模組（auth.py）

負責處理註冊、登入和登出：

註冊 (/register)：從 POST 表單接收使用者名稱、電子信箱與密碼，檢查使用者名稱是否已存在。密碼應使用 Werkzeug 的 generate_password_hash() 進行雜湊儲存。若帳號可用，將新使用者資料寫入 users 表並導向登入頁。

登入 (/login)：從 POST 表單讀取帳號密碼，利用 check_password_hash() 與資料庫中雜湊比對，成功則於 session 中存入 user_id 與 username。

登出 (/logout)：移除 session 資料後重新導向至 Landing Page。

登入限制裝飾器：建立 login_required decorator，若使用者未登入則導向 /login。

2.5 檔案服務模組（file_service.py）

此模組封裝上傳、下載、刪除及列舉檔案的邏輯：

副檔名檢查：函式 allowed_file(filename)，確認檔名含有 . 並且副檔名存在於 ALLOWED_EXTENSIONS。Flask 官方指南建議這樣過濾以避免使用者上傳 HTML 或執行檔。

安全檔名：使用 secure_filename() 產生安全檔名，以防止路徑跳脫攻擊。

上傳檔案：從 request.files['file'] 取得檔案。若檔案大小超過 MAX_CONTENT_LENGTH，Flask 會自動拒絕請求。成功時將檔案以安全檔名儲存於 UPLOAD_FOLDER，並在 files 資料表中建立一筆紀錄（包含檔名、路徑、檔案大小、上傳者 ID、上傳時間）。

列出檔案：查詢 files 表，回傳檔案列表給前端。可加入排序（例如以時間倒序）。

檔案下載：透過 Flask 的 send_from_directory() 根據檔案路徑回傳檔案給使用者。網址規則可為 /download/<int:file_id>。

刪除檔案：確認請求者為檔案擁有者或具備管理權限後，刪除磁碟上的檔案並移除資料庫紀錄。若檔案不存在則回傳錯誤訊息。

2.6 路由與控制器（app.py 或 routes.py）

主要負責 URL 路由與調用各模組函式：

/：Landing Page；若 session 中已有使用者可直接導向 /files。

/register：GET 呈現註冊表單；POST 調用 auth.register()。

/login：類似註冊；POST 調用 auth.login()。

/logout：調用 auth.logout()。

/files：檔案分享主頁；需登入。查詢並顯示檔案列表，並呈現上傳表單。

/upload：處理檔案上傳；使用 file_service.save_file()。

/download/<int:file_id>：下載檔案；調用 file_service.download_file()。

/delete/<int:file_id>：刪除檔案；調用 file_service.delete_file()。

路由中的函式應依照單一責任原則，只負責處理 HTTP 請求與回應，實際商業邏輯封裝在各模組。

2.7 前端模板（templates/）

採用 Jinja2 模板繼承機制，避免重複：

base.html：包含標題、導覽列（登入前顯示「註冊/登入」，登入後顯示使用者名稱及「登出」），並定義 {% block content %} 供子模板覆寫。

landing.html：繼承 base.html，顯示歡迎訊息與兩個按鈕。

register.html：表單包含使用者名稱、Email、密碼、確認密碼等欄位，提交至 /register。

login.html：表單包含使用者名稱及密碼，提交至 /login。

files.html：檔案分享頁。顯示上傳表單（enctype="multipart/form-data" 是上傳表單必須的），提示 50 MB 限制，並列出檔案表格。每一列顯示檔名、檔案大小、上傳者、上傳時間及操作按鈕（下載、刪除）。

3. 資料庫模式與範例 SQL
-- users 資料表
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- files 資料表
CREATE TABLE IF NOT EXISTS files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  filepath TEXT NOT NULL,
  size INTEGER NOT NULL,
  uploaded_by INTEGER NOT NULL,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (uploaded_by) REFERENCES users(id)
);
4. 安全性與擴充建議

密碼雜湊：使用 werkzeug.security.generate_password_hash() 與 check_password_hash() 來儲存與驗證密碼，避免明文儲存。

檔案型別限制：除了副檔名檢查，也可使用 MIME type 檢查（例如 python-magic）。

Session 保護：設定 SECRET_KEY、使用 HTTPS（在 LAN 中可視需求配置自簽證書），避免 session cookie 被竊取。

檔案大小限制：藉由 MAX_CONTENT_LENGTH 阻止超過上限的上傳；範例程式碼中將此值設定為 50 MB。

目錄權限：uploads/ 目錄僅允許後端程式讀寫，避免被瀏覽器直接訪問。

使用者授權：刪除檔案時檢查使用者身份；未來可加入管理者角色，允許管理者移除任何檔案。

擴充性：未來可將 SQLite 換成 MySQL/PostgreSQL、支援多檔案上傳、檔案分類與標籤、分享連結等功能；也可封裝 REST API 供其他應用調用。

5. 總結

本模組化設計將 LAN 檔案分享系統拆分為設定、資料庫、認證、檔案服務、路由與前端模板等獨立模組，各模組間透過明確的介面互動，方便日後維護與擴充。設計時遵循 Flask 官方對檔案上傳的建議：使用 secure_filename() 確保檔名安全、限制檔案大小 (MAX_CONTENT_LENGTH)、限制副檔名等，並以 SQLite 儲存資料。使用者可根據需求使用其他後端或框架實作，但整體模組化結構與安全性措施應保持一致。