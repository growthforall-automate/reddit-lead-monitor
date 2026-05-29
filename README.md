# 🌿 MintOS — AI-Powered Reddit Lead Monitor

> Your local-first, AI-powered CRM for monitoring Reddit leads, qualifying prospects, and managing outreach. Built for solopreneurs and creators who want to grow without paying for bloated SaaS tools.

## Why MintOS?

- **100% Local** — Your data stays on your machine. No cloud lock-in.
- **AI-Powered Lead Scoring** — Uses Claude, GPT, Gemini, or Groq to qualify leads automatically.
- **Reddit Prospecting** — Find and engage potential customers where they hang out.
- **Single Command Setup** — `./start.sh` and you're running.
- **Zero Cost** — No subscriptions. Bring your own API keys.

## Quick Start

```bash
git clone https://github.com/growthforall-automate/reddit-lead-monitor.git
cd reddit-lead-monitor
cp .env.example .env   # Add your API keys
./start.sh             # Opens at http://localhost:8000
```

## Features

| Feature | Description |
|---------|-------------|
| Lead Management | Track, score, and nurture leads with AI assistance |
| AI Brain | Stores your ICP, voice, pain points, and learnings |
| Reddit Integration | Find leads on Reddit, generate contextual replies |
| Multi-LLM Support | Claude, OpenAI, Gemini, Groq — your choice |
| Auth & Security | JWT-based auth, bcrypt passwords |

## Tech Stack

- **Backend:** FastAPI + SQLite + Python 3.10+
- **Frontend:** Vanilla HTML/JS (lightweight, no build step)
- **AI:** Multi-provider LLM support (Anthropic, OpenAI, Google, Groq)

## Configuration

Copy `.env.example` to `.env` and fill in your keys:

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | `claude` / `openai` / `gemini` / `groq` |
| `ANTHROPIC_API_KEY` | If using Claude | Your Anthropic API key |
| `OPENAI_API_KEY` | If using OpenAI | Your OpenAI API key |
| `GEMINI_API_KEY` | If using Gemini | Your Google AI API key |
| `GROQ_API_KEY` | If using Groq | Your Groq API key |
| `REDDIT_CLIENT_ID` | For Reddit features | Reddit app client ID |
| `REDDIT_CLIENT_SECRET` | For Reddit features | Reddit app client secret |

## API Documentation

Once running, visit `http://localhost:8000/api/docs` for the interactive Swagger documentation.

## Contributing

We welcome contributions! Please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## From the Makers

MintOS is built by the team behind **[ThoughtMint](https://thoughtmint.ai)** — a LinkedIn Personal Branding OS.

### 🔗 Our Ecosystem

- 🎬 **YouTube:** [ThoughtMint](https://youtube.com/@ThoughtMint) — AI tutorials & personal branding
- 🌐 **ThoughtMint:** [thoughtmint.ai](https://thoughtmint.ai) — LinkedIn Personal Branding OS
- 🤝 **World Wide Collab:** [worldwidecollab.co](https://worldwidecollab.co) — global builder community
- 🚀 **Visibility Ventures:** [visibilityventures.co](https://visibilityventures.co) — personal brand growth

---

### ⭐ Star this repo if it helps you!

If you find this tool useful, give it a star — it helps others discover the project.

## License

MIT © [ThoughtMint](https://thoughtmint.ai)
