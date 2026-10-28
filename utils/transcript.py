import html
import io
from datetime import datetime
from zoneinfo import ZoneInfo

import discord

import config
from utils.i18n import t

TZ = ZoneInfo(config.TIMEZONE)

CSS = """
body { background:#313338; color:#dbdee1; font-family:'Segoe UI',Helvetica,Arial,sans-serif; margin:0; }
header { background:#2b2d31; padding:20px 28px; border-bottom:1px solid #1e1f22; }
header h1 { margin:0 0 10px; font-size:22px; color:#f2f3f5; }
header .info { display:grid; grid-template-columns:max-content 1fr; gap:4px 14px; font-size:14px; }
header .info b { color:#b5bac1; }
main { padding:16px 28px; }
.msg { display:flex; gap:14px; padding:8px 0; }
.avatar { width:40px; height:40px; border-radius:50%; flex-shrink:0; }
.meta { margin-bottom:3px; }
.author { color:#f2f3f5; font-weight:600; }
.tag { background:#5865f2; color:#fff; font-size:10px; padding:1px 5px; border-radius:3px; margin-left:6px; }
.time { color:#949ba4; font-size:12px; margin-left:8px; }
.content { line-height:1.4; word-wrap:break-word; }
.embed { background:#2b2d31; border-left:4px solid #f5b83d; border-radius:4px; padding:10px 14px; margin-top:6px; max-width:520px; }
.embed .title { font-weight:600; color:#f2f3f5; margin-bottom:6px; }
.embed .field-name { font-weight:600; color:#f2f3f5; margin-top:8px; }
.attachment a { color:#00a8fc; }
footer { color:#949ba4; font-size:12px; text-align:center; padding:20px; }
"""


def _fmt(dt: datetime) -> str:
    return dt.astimezone(TZ).strftime("%d/%m/%Y %H:%M")


def _text(value: str) -> str:
    return html.escape(value).replace("\n", "<br>")


def _render_message(m: discord.Message) -> str:
    parts = []

    if m.content:
        parts.append(f'<div class="content">{_text(m.content)}</div>')

    for e in m.embeds:
        e_parts = []
        if e.title:
            e_parts.append(f'<div class="title">{_text(e.title)}</div>')
        if e.description:
            e_parts.append(f"<div>{_text(e.description)}</div>")
        for f in e.fields:
            e_parts.append(f'<div class="field-name">{_text(f.name)}</div><div>{_text(f.value)}</div>')
        parts.append(f'<div class="embed">{"".join(e_parts)}</div>')

    for a in m.attachments:
        parts.append(
            f'<div class="attachment">📎 <a href="{html.escape(a.url)}">{html.escape(a.filename)}</a></div>'
        )

    bot_tag = '<span class="tag">BOT</span>' if m.author.bot else ""
    return (
        f'<div class="msg">'
        f'<img class="avatar" src="{html.escape(m.author.display_avatar.url)}" alt="">'
        f'<div><div class="meta"><span class="author">{html.escape(m.author.display_name)}</span>'
        f'{bot_tag}<span class="time">{_fmt(m.created_at)}</span></div>'
        f'{"".join(parts)}</div></div>'
    )


async def build_transcript(
    channel: discord.TextChannel,
    issuer: str,
    closer: str,
    opened_at: datetime,
    closed_at: datetime,
) -> discord.File:
    rows = [_render_message(m) async for m in channel.history(limit=None, oldest_first=True)]

    info = [
        (t("transcript.issuer"), issuer),
        (t("transcript.closed_by"), closer),
        (t("transcript.opened_at"), _fmt(opened_at)),
        (t("transcript.closed_at"), _fmt(closed_at)),
        (t("transcript.messages"), str(len(rows))),
    ]
    info_html = "".join(f"<b>{html.escape(k)}</b><span>{html.escape(v)}</span>" for k, v in info)

    page = (
        f'<!doctype html><html lang="{config.LANGUAGE}"><head><meta charset="utf-8">'
        f"<title>{html.escape(channel.name)}</title><style>{CSS}</style></head><body>"
        f"<header><h1>📄 {html.escape(channel.name)}</h1><div class='info'>{info_html}</div></header>"
        f"<main>{''.join(rows)}</main>"
        f"<footer>{html.escape(t('transcript.footer'))}</footer></body></html>"
    )

    return discord.File(io.BytesIO(page.encode("utf-8")), filename=f"{channel.name}.html")