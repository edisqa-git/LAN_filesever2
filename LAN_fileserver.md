# LAN File Sharing System Modular Design

Scenario: users on the same local area network (LAN) need a simple file-sharing website. From the landing page, a visitor can choose `Sign Up` or `Sign In`. After signing in, the user is taken to the file-sharing page. Users can upload files up to 50 MB, download files, delete only the files they uploaded, and view a file list with basic metadata. The system should use a lightweight database such as SQLite and follow a modular design so it is easy to extend and maintain.

## 1. Architecture Overview

The application follows an MVC-style structure that can be divided into four layers: frontend interface, backend services, database, and file storage.

- View: provides HTML, CSS, and client-side behavior for signup, signin, and file-sharing pages. A template engine such as Flask Jinja2 keeps layout separate from data.
- Controller: handles routes, authentication, upload, download, delete, and bulletin board interactions. It coordinates the database and file service modules.
- Model: stores user data, file metadata, bulletin posts, and bulletin replies in SQLite.
- File storage: actual files are saved under `uploads/`. A file service module manages file naming, saving, and deletion. Flask recommends `secure_filename()` to avoid unsafe paths and filename injection.

## 1.1 System Flow

- Unauthenticated visitors who access `/` see the landing page with `Sign Up` and `Sign In`.
- `Sign Up` sends the user to `/register`, where the backend verifies the username is available and stores the account with a hashed password.
- `Sign In` sends the user to `/login`, where the backend validates the password hash, creates a session, and redirects the user to `/files`.
- Authenticated users visiting `/files` see:
  - the signed-in username and a `Sign Out` button
  - a 50 MB upload limit notice
  - file selection and upload controls
  - a file table listing filename, size, uploader, upload time, and actions
  - the sticky-note bulletin board for posting and replying
- Clicking `Download` returns the file via `send_from_directory()`.
- Clicking `Delete` verifies ownership before removing the file from disk and deleting its database record.
- Clicking `Sign Out` clears the session and returns the user to the landing page.

## 2. Modular Breakdown

The example below assumes Python and Flask, but the same modular boundaries apply to other stacks such as Node.js with Express.

## 2.1 Example Project Structure

```text
├── app.py              # app startup and route registration
├── config.py           # settings such as secret key, upload path, size limit
├── db.py               # database connection and query helpers
├── auth.py             # signup, signin, signout logic
├── file_service.py     # upload, download, delete, file type validation
├── bulletin_service.py # bulletin post and reply logic
├── templates/          # Jinja templates: base.html, login.html, register.html, files.html
├── static/             # static assets: CSS and JS
└── uploads/            # uploaded files
```

## 2.2 Settings and Constants

- `SECRET_KEY`: used for Flask session signing.
- `UPLOAD_FOLDER`: the directory where uploaded files are stored.
- `MAX_CONTENT_LENGTH`: limits the HTTP request body size. In Flask, this raises `RequestEntityTooLarge` when exceeded. This project uses `50 * 1024 * 1024`.
- `ALLOWED_EXTENSIONS`: the allowed file extension set, such as `txt`, `pdf`, `png`, `jpg`, `jpeg`, `gif`, `json`, and network capture formats.

## 2.3 Database Module (`db.py`)

This module is responsible for:

- opening the SQLite connection with `sqlite3.connect()`
- enabling `row_factory` for dictionary-style row access
- creating tables during app startup
- exposing shared `query_one`, `query_all`, and `execute` helpers

Core tables:

- `users`: `id`, `username`, `email`, `password_hash`, `created_at`
- `files`: `id`, `filename`, `filepath`, `size`, `uploaded_by`, `uploaded_at`
- `bulletin_posts`: `id`, `title`, `body`, `created_by`, `created_at`
- `bulletin_comments`: `id`, `post_id`, `parent_comment_id`, `body`, `created_by`, `created_at`

## 2.4 Authentication Module (`auth.py`)

Responsibilities:

- `POST /register`: accepts username, email, password, and confirmation, checks for duplicate usernames, hashes the password with `generate_password_hash()`, and stores the account.
- `POST /login`: validates the provided password with `check_password_hash()` and stores `user_id` and `username` in the session.
- `POST /logout`: clears the session and redirects back to the landing page.
- `login_required`: redirects unauthenticated users to `/login`.

## 2.5 File Service Module (`file_service.py`)

This module encapsulates upload, listing, download, and delete behavior.

- Extension validation: `allowed_file(filename)` ensures the extension is in `ALLOWED_EXTENSIONS`.
- Safe filenames: `secure_filename()` avoids path traversal and unsafe names.
- Upload handling: reads the uploaded file from `request.files["file"]`, saves it to `UPLOAD_FOLDER`, and inserts a file record into the database.
- File listing: queries the `files` table and returns rows to the template.
- Download: resolves the saved path and returns the file to the browser.
- Delete: ensures only the uploader can remove the file, then deletes both the disk file and database row.

## 2.6 Bulletin Board Module (`bulletin_service.py`)

This module supports the sticky-note discussion board.

- Post creation: validates a title and post body, then inserts a row into `bulletin_posts`.
- Reply creation: validates the reply body, confirms the target post exists, and optionally attaches the reply to a parent comment.
- Thread loading: returns posts with top-level comments and one reply layer for rendering in the template.

## 2.7 Routes and Controllers (`app.py`)

Primary routes:

- `/`: landing page, redirecting signed-in users to `/files`
- `/register`: render and submit signup
- `/login`: render and submit signin
- `/logout`: sign out
- `/files`: authenticated file-sharing and bulletin board page
- `/upload`: handle file uploads
- `/download/<int:file_id>`: download a file
- `/delete/<int:file_id>`: delete a file
- `/bulletin/posts`: create a bulletin post
- `/bulletin/posts/<int:post_id>/comments`: create a reply or nested reply

Each route should stay focused on HTTP request and response handling, while the main business logic remains in dedicated modules.

## 2.8 Frontend Templates (`templates/`)

The project uses Jinja template inheritance to avoid duplication.

- `base.html`: common layout, navigation, and flash message container
- `landing.html`: welcome content and entry actions
- `register.html`: signup form
- `login.html`: signin form
- `files.html`: file upload UI, file table, and sticky-note bulletin board

The file page should display:

- upload controls with `multipart/form-data`
- accepted file type and size guidance
- a table of uploaded files
- download and delete actions
- sticky-note bulletin cards with replies

## 3. Example SQL Schema

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  filepath TEXT NOT NULL,
  size INTEGER NOT NULL,
  uploaded_by INTEGER NOT NULL,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

CREATE TABLE bulletin_posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  created_by INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE bulletin_comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL,
  parent_comment_id INTEGER,
  body TEXT NOT NULL,
  created_by INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (post_id) REFERENCES bulletin_posts(id),
  FOREIGN KEY (parent_comment_id) REFERENCES bulletin_comments(id),
  FOREIGN KEY (created_by) REFERENCES users(id)
);
```

## 4. Security and Extension Notes

- Password hashing: always store and verify passwords with Werkzeug hash helpers.
- File type restrictions: extension filtering is required, and MIME validation can be added later if needed.
- Session protection: configure a production-grade `SECRET_KEY` and run HTTPS where appropriate.
- File size protection: `MAX_CONTENT_LENGTH` blocks oversized uploads before they are processed.
- Directory permissions: `uploads/` should be writable only by the backend process.
- Authorization: file deletion should remain owner-only unless an admin role is added later.
- Extensibility: the project can later move from SQLite to MySQL or PostgreSQL, support multi-file uploads, tagging, sharing links, or a REST API.

## 5. Summary

This modular design separates configuration, database access, authentication, file handling, bulletin board logic, routes, and frontend templates into focused units. The result is easier to maintain and safer to extend. The implementation should keep following Flask best practices around filename sanitization, upload size enforcement, authenticated access, and ownership checks.
