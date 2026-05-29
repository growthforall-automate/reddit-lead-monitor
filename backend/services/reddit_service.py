import os
import re
from backend.config import BRAIN_DIR


def get_keywords_from_brain() -> list[str]:
    """Extract signal keywords from pain_points.md."""
    path = os.path.join(BRAIN_DIR, "pain_points.md")
    if not os.path.exists(path):
        # FIX: Broadened fallback keywords relevant to ThoughtMint/content/SaaS
        return [
            "linkedin", "personal brand", "content ideas", "what to post",
            "thought leadership", "ghostwriter", "content creation", "build in public",
            "grow my audience", "creator economy", "newsletter", "solopreneur",
            "indie hacker", "saas founder", "content strategy", "social media",
            "audience growth", "twitter", "posting consistently", "content calendar",
        ]
    with open(path) as f:
        text = f.read()
    # Find the "Reddit Signal Keywords" section
    match = re.search(r"Reddit Signal Keywords.*?\n(.*?)(?:\n#|\Z)", text, re.DOTALL | re.IGNORECASE)
    if match:
        kw_text = match.group(1)
        keywords = [k.strip() for k in re.split(r"[,\n]", kw_text) if k.strip()]
        return keywords[:30]
    # Fallback: extract quoted phrases, then broad defaults
    found = re.findall(r'"([^"]+)"', text)[:20]
    return found or [
        "linkedin", "personal brand", "content ideas", "what to post",
        "thought leadership", "ghostwriter", "content creation", "build in public",
        "grow my audience", "creator economy", "newsletter", "solopreneur",
        "indie hacker", "saas founder", "content strategy", "social media",
        "audience growth", "twitter", "posting consistently", "content calendar",
    ]


def post_matches_keywords(title: str, body: str, keywords: list[str]) -> bool:
    text = (title + " " + (body or "")).lower()
    return any(kw.lower() in text for kw in keywords)


def scan_subreddits(settings: dict) -> list[dict]:
    """Scan subreddits using PRAW and return matching posts."""
    try:
        import praw
    except ImportError:
        raise RuntimeError("praw is not installed. Run: pip install praw")

    client_id      = settings.get("reddit_client_id", "").strip()
    client_secret  = settings.get("reddit_client_secret", "").strip()
    user_agent     = settings.get("reddit_user_agent", "MintOS/1.0 by ThoughtMint").strip()
    subreddits_raw = settings.get("reddit_subreddits", "entrepreneur,indiehackers,SaaS,marketing,Entrepreneur")
    limit          = int(settings.get("reddit_scan_limit", "50"))
    min_score      = int(settings.get("reddit_min_score", "0"))

    if not all([client_id, client_secret]):
        raise ValueError("Reddit client_id and client_secret are not configured. Set them in Settings.")

    # FIX: Use read-only (application-only OAuth) — works with ANY app type including
    # "web app". No username/password needed. Reddit's Responsible Builder Policy
    # removed password auth for non-script apps, so this is the correct approach
    # for scanning/reading public posts.
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    # Explicitly set read-only so PRAW doesn't attempt password auth
    reddit.read_only = True

    keywords = get_keywords_from_brain()
    print(f"[Reddit] Scanning with {len(keywords)} keywords: {keywords[:5]}...")

    subreddits = [s.strip() for s in subreddits_raw.split(",") if s.strip()]
    results = []
    seen_ids = set()
    scan_errors = []

    for sub_name in subreddits:
        try:
            sub = reddit.subreddit(sub_name)

            # FIX: scan both new AND hot to catch more relevant posts
            # new = freshest leads, hot = already-validated conversations
            streams = [
                ("new", sub.new(limit=limit)),
                ("hot", sub.hot(limit=limit // 2)),
            ]

            for feed_type, stream in streams:
                for post in stream:
                    if post.id in seen_ids:
                        continue
                    # FIX: skip score filter entirely on 'new' feed — new posts
                    # legitimately have score 0–2 and are still valuable leads
                    if feed_type == "hot" and post.score < min_score:
                        continue
                    if post.over_18 or post.stickied:
                        continue
                    if not post_matches_keywords(post.title, post.selftext or "", keywords):
                        continue
                    seen_ids.add(post.id)
                    results.append({
                        "post_id":    post.id,
                        "subreddit":  sub_name,
                        "post_title": post.title[:300],
                        "post_url":   f"https://reddit.com{post.permalink}",
                        "post_body":  (post.selftext or "")[:1500],
                        "author":     str(post.author) if post.author else "[deleted]",
                        "post_score": post.score,
                    })

        except Exception as e:
            err = f"r/{sub_name}: {e}"
            print(f"[Reddit] Error scanning {err}")
            scan_errors.append(err)
            continue  # keep scanning remaining subreddits

    # FIX: if every subreddit failed, surface a meaningful error
    if scan_errors and not results:
        raise RuntimeError(
            f"All subreddits failed to scan. Errors: {' | '.join(scan_errors)}"
        )

    print(f"[Reddit] Scan complete — {len(results)} matching posts found across {len(subreddits)} subreddits")
    return results
