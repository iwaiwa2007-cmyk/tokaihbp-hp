#!/usr/bin/env python3
"""Send abstract-deadline alerts 30 days before and on the deadline date."""

from __future__ import annotations

import argparse
import json
import os
import smtplib
from datetime import date, datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DEADLINES_FILE = ROOT / "events" / "abstract-deadlines.json"
RECIPIENT = "iwaiwa2007@gmail.com"
JAPAN_TIME = ZoneInfo("Asia/Tokyo")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="確認日（YYYY-MM-DD）。省略時は日本時間の今日")
    parser.add_argument("--dry-run", action="store_true", help="送信せず対象メールを表示")
    return parser.parse_args()


def load_deadlines() -> list[dict[str, str]]:
    return json.loads(DEADLINES_FILE.read_text(encoding="utf-8"))


def build_message(item: dict[str, str], days_left: int, sender: str) -> EmailMessage:
    timing = "本日締切" if days_left == 0 else "締切30日前"
    subject = f"【演題締切アラート・{timing}】{item['event']}"
    body = (
        f"{item['event']}の演題・抄録締切のお知らせです。\n\n"
        f"締切：{item['deadline_label']}\n"
        f"登録・確認ページ：{item['url']}\n\n"
        "日程が変更される場合がありますので、登録前に公式ページをご確認ください。\n"
    )
    message = EmailMessage()
    message["From"] = sender
    message["To"] = RECIPIENT
    message["Subject"] = subject
    message.set_content(body)
    return message


def main() -> int:
    args = parse_args()
    today = date.fromisoformat(args.date) if args.date else datetime.now(JAPAN_TIME).date()
    sender = os.environ.get("GMAIL_USERNAME", "").strip()
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")

    due_items: list[tuple[dict[str, str], int]] = []
    for item in load_deadlines():
        deadline = date.fromisoformat(item["deadline"])
        days_left = (deadline - today).days
        if days_left in (30, 0):
            due_items.append((item, days_left))

    if not due_items:
        print(f"{today.isoformat()}: 送信対象の締切はありません。")
        return 0

    if args.dry_run:
        preview_sender = sender or "GMAIL_USERNAME"
        for item, days_left in due_items:
            print(build_message(item, days_left, preview_sender))
        return 0

    if not sender or not app_password:
        raise RuntimeError("GitHub SecretsのGMAIL_USERNAMEとGMAIL_APP_PASSWORDを設定してください。")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, app_password)
        for item, days_left in due_items:
            smtp.send_message(build_message(item, days_left, sender))
            print(f"送信しました: {item['event']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
