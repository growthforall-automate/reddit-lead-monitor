import httpx
import json
import os
from backend.config import BRAIN_DIR


def load_brain() -> str:
    files = ["context.md", "icp.md", "pain_points.md", "voice.md", "learnings.md"]
    parts = []
    for f in files:
        path = os.path.join(BRAIN_DIR, f)
        if os.path.exists(path):
            with open(path) as fh:
                parts.append(f"## {f}\n{fh.read()}")
    return "\n\n".join(parts)


def detect_provider(settings: dict) -> str:
    explicit = settings.get("llm_provider", "").strip()
    if explicit:
        key_map = {"claude": "anthropic_api_key", "openai": "openai_api_key",
                   "groq": "groq_api_key", "gemini": "gemini_api_key"}
        required_key = key_map.get(explicit, "")
        if required_key and settings.get(required_key, "").strip():
            return explicit
    if settings.get("anthropic_api_key", "").strip():
        return "claude"
    if settings.get("groq_api_key", "").strip():
        return "groq"
    if settings.get("openai_api_key", "").strip():
        return "openai"
    if settings.get("gemini_api_key", "").strip():
        return "gemini"
    return "groq"


def _post_field(post: dict, snake: str, camel: str) -> str:
    value = post.get(snake) or post.get(camel) or ""
    return value if isinstance(value, str) else str(value)


def build_dm_prompts(post: dict) -> tuple[str, str]:
    brain = load_brain()
    system = (
        "You are Ayush Gupta, founder of ThoughtMint.ai — a LinkedIn Personal Branding platform.\n"
        "ThoughtMint helps founders, coaches, consultants and executives:\n"
        "- Generate LinkedIn content ideas\n"
        "- Write full LinkedIn posts in their voice using AI\n"
        "- Create LinkedIn carousels automatically\n"
        "- Stay consistent on LinkedIn without spending hours\n\n"
        "CONTEXT:\n" + brain + "\n\n"
        "YOUR DEFAULT ACTION IS TO WRITE A DM. You write a DM for almost every post.\n\n"
        "The ONLY time you output SKIP is when the post is CLEARLY about:\n"
        "- Someone looking for a job or internship\n"
        "- A company hiring/recruiting employees\n"
        "- A purely technical LinkedIn bug (e.g. 'why can't I log in')\n"
        "Everything else — write a DM. If you are unsure, write the DM.\n\n"
        "WHEN YOU SKIP, format it as: SKIP: [one sentence explaining why this person is not a ThoughtMint prospect]\n\n"
        "HOW TO WRITE A GREAT DM:\n"
        "1. Open with ONE specific detail from their post — quote their number, their exact situation, or their words\n"
        "2. Connect ThoughtMint directly to that specific thing — name the feature\n"
        "3. End with https://thoughtmint.ai\n"
        "4. Max 3 sentences. Founder voice, not sales voice.\n"
        "5. Never say: 'I saw your post', 'I came across', 'Hope this finds you', 'struggling with content creation can be'\n\n"
        "EXAMPLES OF GOOD DMs:\n\n"
        "Post: LinkedIn reach dropped from 90k to almost nothing\n"
        "DM: PixelPoet — going from 90k impressions to flatline with the same content usually means the algorithm wants more format variety. ThoughtMint generates carousel ideas, hook-led posts, and story formats so your content mix stays fresh: https://thoughtmint.ai\n\n"
        "Post: Founder spending 10-12 hours/week on content\n"
        "DM: Virginia, 10-12 hours a week on content is brutal for a solo consultant. ThoughtMint writes LinkedIn posts and carousels in your voice automatically — most users get it under an hour a week: https://thoughtmint.ai\n\n"
        "Post: Don't know what to post on LinkedIn\n"
        "DM: That blank-page feeling every week is exactly what ThoughtMint kills — it generates a full week of LinkedIn ideas based on your niche in under a minute: https://thoughtmint.ai\n\n"
        "Post: Founder wants to grow LinkedIn audience\n"
        "DM: Growing a LinkedIn audience as a founder while building the product is a consistency game — ThoughtMint keeps you showing up with fresh posts and carousels without the time cost: https://thoughtmint.ai"
    )
    user = (
        f"Write a DM for this Reddit post. Default is to write the DM — only output SKIP: [reason] if it is 100% clearly a job seeker, recruiter, or technical bug report.\n\n"
        f"Subreddit: r/{post.get('subreddit', '')}\n"
        f"Author: u/{post.get('author', '')}\n"
        f"Title: {_post_field(post, 'post_title', 'postTitle')}\n\n"
        f"Post:\n{_post_field(post, 'post_body', 'postBody')[:1500]}\n\n"
        f"Reference something specific from this post. Output only the DM or SKIP: [reason]:"
    )
    return system, user


def build_score_prompt(post: dict, brain: str) -> tuple[str, str]:
    system = (
        "You are scoring Reddit posts for ThoughtMint.ai — a LinkedIn Personal Branding platform.\n"
        "ThoughtMint helps founders, coaches, consultants and executives create consistent LinkedIn content using AI.\n\n"
        + brain + "\n\n"
        "Score 8-10: Person explicitly struggles with LinkedIn content, consistency, ideas, carousels, or personal branding.\n"
        "Score 6-7: Founder/coach/consultant/executive who would benefit from LinkedIn presence.\n"
        "Score 4-5: In the right space but no clear content pain point.\n"
        "Score 1-3: Not relevant.\n\n"
        'Respond ONLY with valid JSON: {"score": 7.5, "reason": "one sentence", "pain_point": "brief label"}'
    )
    user = (
        f"Score this post:\n\n"
        f"Subreddit: r/{post.get('subreddit', '')}\n"
        f"Title: {_post_field(post, 'post_title', 'postTitle')}\n"
        f"Content: {_post_field(post, 'post_body', 'postBody')[:800]}\n\n"
        f"JSON only:"
    )
    return system, user


async def generate_dm(post: dict, settings: dict) -> str:
    provider = detect_provider(settings)
    model = settings.get("llm_model", "").strip()
    system, user = build_dm_prompts(post)
    try:
        if provider == "openai":
            return await _call_openai(system, user, model or "gpt-4o", settings.get("openai_api_key", ""))
        elif provider == "claude":
            return await _call_claude(system, user, model or "claude-sonnet-4-6", settings.get("anthropic_api_key", ""))
        elif provider == "gemini":
            return await _call_gemini(system, user, model or "gemini-1.5-pro", settings.get("gemini_api_key", ""))
        elif provider == "groq":
            return await _call_openai_compat(system, user, model or "llama-3.3-70b-versatile",
                                             settings.get("groq_api_key", ""), "https://api.groq.com/openai/v1")
        else:
            raise ValueError("No valid LLM provider configured.")
    except Exception as e:
        raise RuntimeError(f"DM generation failed ({provider}): {e}") from e


async def score_post(post: dict, settings: dict) -> dict:
    brain = load_brain()
    provider = detect_provider(settings)
    model = settings.get("llm_model", "").strip()
    system, user = build_score_prompt(post, brain)
    try:
        if provider == "openai":
            text = await _call_openai(system, user, model or "gpt-4o-mini", settings.get("openai_api_key", ""))
        elif provider == "claude":
            text = await _call_claude(system, user, model or "claude-haiku-4-5-20251001", settings.get("anthropic_api_key", ""))
        elif provider == "groq":
            text = await _call_openai_compat(system, user, model or "llama-3.1-8b-instant",
                                             settings.get("groq_api_key", ""), "https://api.groq.com/openai/v1")
        elif provider == "gemini":
            text = await _call_gemini(system, user, model or "gemini-1.5-flash", settings.get("gemini_api_key", ""))
        else:
            return {"score": 5.0, "reason": "No LLM provider configured", "pain_point": "Unknown"}
        text = text.strip().strip("```json").strip("```").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[LLM] Scoring failed: {e}")
        return {"score": 5.0, "reason": "Could not score automatically", "pain_point": "Unknown"}


async def update_learnings(event: str, details: dict, settings: dict) -> None:
    path = os.path.join(BRAIN_DIR, "learnings.md")
    if not os.path.exists(path):
        return
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    if event == "dm_sent":
        entry = f"\n[{date}] DM Sent | r/{details.get('subreddit')} | Pain: {details.get('pain_point')} | Post: {details.get('post_title', '')[:60]}"
        section = "## DM Learnings"
    elif event == "status_changed":
        entry = f"\n[{date}] Status: {details.get('from_status')} → {details.get('to_status')} | r/{details.get('subreddit')}"
        section = "## DM Learnings"
    elif event == "scan_complete":
        entry = f"\n[{date}] Scan | Found: {details.get('found')} | Inserted: {details.get('inserted')}"
        section = "## Subreddit Performance"
    else:
        return
    try:
        with open(path, "r") as f:
            content = f.read()
        if section in content:
            content = content.replace(section, section + entry, 1)
        else:
            content += f"\n{section}{entry}\n"
        with open(path, "w") as f:
            f.write(content)
    except Exception as e:
        print(f"[Learnings] Failed to update: {e}")


async def _call_openai(system: str, user: str, model: str, api_key: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "max_tokens": 500})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()


async def _call_claude(system: str, user: str, model: str, api_key: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json={"model": model, "max_tokens": 500, "system": system, "messages": [{"role": "user", "content": user}]})
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()


async def _call_gemini(system: str, user: str, model: str, api_key: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": f"{system}\n\n{user}"}]}], "generationConfig": {"maxOutputTokens": 500}})
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


async def _call_openai_compat(system: str, user: str, model: str, api_key: str, base_url: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "max_tokens": 500})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
