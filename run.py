"""CLI entry point: python run.py [--dry-run|--live] [--limit N]"""

import argparse
import yaml

from email_agent.agent import InboxAgent


def main():
    parser = argparse.ArgumentParser(description="AI Email Agent")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--limit", type=int, default=20)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                      help="preview only, change nothing (default)")
    mode.add_argument("--live", dest="dry_run", action="store_false",
                      help="actually file drafts and archive")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    agent = InboxAgent(
        host=cfg["imap"]["host"],
        email_addr=cfg["imap"]["email"],
        password=cfg["imap"]["app_password"],
        use_llm=cfg.get("classifier", {}).get("use_llm", False),
        llm_model=cfg.get("classifier", {}).get("llm_model", "llama3.1"),
    )

    mode_name = "DRY-RUN" if args.dry_run else "LIVE"
    print(f"--- AI Email Agent ({mode_name}) ---")
    for subject, label, action in agent.run(limit=args.limit, dry_run=args.dry_run):
        print(f"[{label.upper():8s}] {subject}")
        print(f"           -> {action}")
    print("--- done ---")


if __name__ == "__main__":
    main()
