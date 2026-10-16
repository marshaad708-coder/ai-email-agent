# AI Email Agent

> Watch it in action: [YouTube video](https://www.youtube.com/) *(link your Day 1 video here)*

An AI agent that reads your inbox, sorts incoming mail into **urgent / spam / personal**,
and **drafts replies** for the urgent ones. You stay in control — nothing is ever sent
without your approval.

Built with plain Python + IMAP. No paid APIs required. An optional Ollama LLM makes
the classification smarter if you have it running locally.

## Features

- Reads unread mail over IMAP (works with Gmail via app password)
- Rule-based classifier out of the box, optional Ollama LLM fallback
- **Dry-run mode (default):** prints what it *would* do, changes nothing
- Drafts replies for urgent mail, archives newsletters and spam
- Single YAML config, no database

## Quickstart

```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml   # then fill in your email + app password
python run.py --dry-run              # safe preview, changes nothing
python run.py --live                 # actually files drafts / archives
```

## How it works

1. Connects to your inbox over IMAP and fetches unread messages.
2. Each message is classified as `urgent`, `spam`, or `personal`.
3. `urgent` → a reply draft is created in your Drafts folder for you to review.
4. `spam` → archived. `personal` → left alone (optionally labeled).

In `--dry-run` mode every action is printed and nothing is written.

## Config

See `config.example.yaml`. Never commit your real `config.yaml` —
it is already in `.gitignore`.

## Safety

- Use a Gmail **app password**, never your main password.
- Always review drafts before sending. The agent drafts, you decide.
