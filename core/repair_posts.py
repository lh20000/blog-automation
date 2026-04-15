# =============================================
# repair_posts.py — Fix and republish posts
# Searches LIVE + DRAFT, fixes HTML, republishes
# =============================================

import re
import sys
import os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import BLOG_ID, TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/blogger"]

TARGET_KEYWORDS = ["stock market"]


def get_credentials():
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
            print("Token refreshed.")
    return creds


def fix_html(html: str) -> str:
    original = html

    # 1. Convert <b>Step N: heading</b> → <h3> before stripping bold
    html = re.sub(
        r'<b[^>]*>((?:Step|Phase)\s*\d+[:.][^<]{3,})</b>',
        r'<h3 style="margin-top:24px;">\1</h3>',
        html, flags=re.IGNORECASE,
    )

    # 2. Strip all <b> / <strong> tags (keep text content)
    html = re.sub(r'</?(?:b|strong)(?:\s[^>]*)?>', '', html)

    # 3. Move img2: second centered-image div → before Expert Tip box
    img_pattern = re.compile(
        r'<div[^>]*text-align:center[^>]*>(?:\s*)<img[^>]*>(?:\s*)</div>',
        re.DOTALL | re.IGNORECASE,
    )
    img_matches = list(img_pattern.finditer(html))
    print(f"  [Fix] Image divs found: {len(img_matches)}")

    if len(img_matches) >= 2:
        img2        = img_matches[1]
        img2_html   = img2.group(0)
        html        = html[:img2.start()] + html[img2.end():]

        tip_match = re.search(r'<div[^>]*background:#fff8e1', html, re.IGNORECASE)
        if tip_match:
            pos  = tip_match.start()
            html = html[:pos] + img2_html + "\n" + html[pos:]
            print("  [Fix] img2 moved → before Expert Tip box ✅")
        else:
            print("  [Fix] Expert Tip box not found — img2 left in place")

    changed = html != original
    print(f"  [Fix] HTML {'changed' if changed else 'no changes detected'}")
    return html


def find_target_posts(service) -> list:
    """Search LIVE and DRAFT posts for target keywords."""
    found = {}

    for status in ("live", "draft"):
        try:
            resp = service.posts().list(
                blogId=BLOG_ID,
                status=status.upper(),
                view="ADMIN",
                maxResults=50,
            ).execute()
        except Exception as e:
            print(f"  [Search] {status} list error: {e}")
            continue

        for post in resp.get("items", []):
            title = post.get("title", "").lower()
            pid   = post["id"]
            if any(kw in title for kw in TARGET_KEYWORDS) and pid not in found:
                found[pid] = post
                print(f"  Found [{status.upper()}]: {post['title']} (id={pid})")

    return list(found.values())


def repair_and_publish(service, post: dict) -> bool:
    post_id = post["id"]
    title   = post["title"]
    status  = post.get("status", "?")

    print(f"\n{'─'*52}")
    print(f"  Title : {title}")
    print(f"  ID    : {post_id}  Status: {status}")

    # Step 1: Revert to draft if currently LIVE
    if status == "LIVE":
        try:
            service.posts().revert(blogId=BLOG_ID, postId=post_id).execute()
            print("  [Step 1] Reverted to draft")
        except Exception as e:
            print(f"  [Step 1] Revert failed: {e}")
            return False
    else:
        print("  [Step 1] Already draft — skip revert")

    # Step 2: Fetch full content (revert clears content field)
    try:
        post_full = service.posts().get(
            blogId=BLOG_ID, postId=post_id, view="ADMIN"
        ).execute()
    except Exception as e:
        print(f"  [Step 2] Get post failed: {e}")
        return False

    content = post_full.get("content", "")
    print(f"  [Step 2] Content fetched ({len(content)} chars)")

    # Step 3: Fix HTML
    fixed = fix_html(content)

    # Step 4: Patch with fixed content
    try:
        service.posts().patch(
            blogId=BLOG_ID,
            postId=post_id,
            body={"content": fixed},
        ).execute()
        print("  [Step 4] Content patched ✅")
    except Exception as e:
        print(f"  [Step 4] Patch failed: {e}")
        return False

    # Step 5: Publish
    try:
        result = service.posts().publish(
            blogId=BLOG_ID, postId=post_id
        ).execute()
        url = result.get("url", "")
        print(f"  [Step 5] Published ✅  {url}")
    except Exception as e:
        print(f"  [Step 5] Publish failed: {e}")
        return False

    return True


def main():
    if not BLOG_ID:
        print("❌ BLOG_ID not set.")
        sys.exit(1)

    print("\n" + "█" * 52)
    print("  repair_posts — Fix & Republish")
    print("█" * 52)

    creds   = get_credentials()
    service = build("blogger", "v3", credentials=creds)

    print("\n[Search] Looking for target posts...")
    targets = find_target_posts(service)

    if not targets:
        print("❌ No target posts found.")
        sys.exit(1)

    print(f"\n[Repair] Processing {len(targets)} post(s)...")
    success = 0
    for post in targets:
        if repair_and_publish(service, post):
            success += 1

    print(f"\n{'█'*52}")
    print(f"  Done: {success}/{len(targets)} republished")
    print("█" * 52)

    if success < len(targets):
        sys.exit(1)


if __name__ == "__main__":
    main()
