from collections import defaultdict

from db import execute, query_all, query_one


POST_TITLE_LIMIT = 120
POST_BODY_LIMIT = 1000
COMMENT_BODY_LIMIT = 600


def _validate_text(value: str, field_name: str, limit: int) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    if len(cleaned) > limit:
        raise ValueError(f"{field_name} must be {limit} characters or fewer.")
    return cleaned


def create_post(title: str, body: str, user_id: int) -> int:
    clean_title = _validate_text(title, "Post title", POST_TITLE_LIMIT)
    clean_body = _validate_text(body, "Post content", POST_BODY_LIMIT)
    return execute(
        "INSERT INTO bulletin_posts (title, body, created_by) VALUES (?, ?, ?)",
        (clean_title, clean_body, user_id),
    )


def create_comment(post_id: int, body: str, user_id: int, parent_comment_id: int | None = None) -> int:
    post = query_one("SELECT id FROM bulletin_posts WHERE id = ?", (post_id,))
    if post is None:
        raise ValueError("Post not found.")

    clean_body = _validate_text(body, "Reply", COMMENT_BODY_LIMIT)

    if parent_comment_id is not None:
        parent = query_one(
            "SELECT id, post_id FROM bulletin_comments WHERE id = ?",
            (parent_comment_id,),
        )
        if parent is None or parent["post_id"] != post_id:
            raise ValueError("Reply target not found.")

    return execute(
        """
        INSERT INTO bulletin_comments (post_id, parent_comment_id, body, created_by)
        VALUES (?, ?, ?, ?)
        """,
        (post_id, parent_comment_id, clean_body, user_id),
    )


def list_posts():
    posts = query_all(
        """
        SELECT p.id, p.title, p.body, p.created_at, p.created_by, u.username
        FROM bulletin_posts AS p
        JOIN users AS u ON p.created_by = u.id
        ORDER BY p.created_at DESC, p.id DESC
        """
    )
    comments = query_all(
        """
        SELECT c.id, c.post_id, c.parent_comment_id, c.body, c.created_at, c.created_by, u.username
        FROM bulletin_comments AS c
        JOIN users AS u ON c.created_by = u.id
        ORDER BY c.created_at ASC, c.id ASC
        """
    )

    replies_by_parent = defaultdict(list)
    comments_by_post = defaultdict(list)

    for row in comments:
        comment = dict(row)
        comment["replies"] = []
        replies_by_parent[comment["parent_comment_id"]].append(comment)

    for comment in replies_by_parent[None]:
        comment["replies"] = replies_by_parent.get(comment["id"], [])
        comments_by_post[comment["post_id"]].append(comment)

    bulletin_posts = []
    for row in posts:
        post = dict(row)
        post["comments"] = comments_by_post.get(post["id"], [])
        bulletin_posts.append(post)

    return bulletin_posts
