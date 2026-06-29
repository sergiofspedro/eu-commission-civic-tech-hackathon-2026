"""EU CivicConnect Telegram Bot — webhook mode on port 8100."""
import logging, os, sys

sys.path.insert(0, "/app/shared")
from consultations import CONSULTATIONS, EU_RESULT
from database import init_db, record_vote, record_opinion, has_voted, has_voted_all, get_vote_counts, get_total_participants
from llm import get_reply

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

TOKEN = os.environ["CIVICCONNECT_TELEGRAM_TOKEN"]
DOMAIN = os.environ.get("PUBLIC_DOMAIN", "your-domain.com")
CONSULTATION_IDS = list(CONSULTATIONS.keys())

# In-memory state: user waiting to send opinion for a consultation
_awaiting_opinion: dict[int, str] = {}


# ── Card builders ─────────────────────────────────────────────────────────────

def _consultation_card(c: dict, voted: bool = False) -> tuple[str, InlineKeyboardMarkup]:
    status = "🟢 Open" if c["status"] == "open" else "🔴 Closed"
    text = (
        f"{c['level_emoji']} *{c['level']} Consultation*\n"
        f"*{c['title']}*\n\n"
        f"{c['summary']}\n\n"
        f"📅 Deadline: {c['deadline']}\n"
        f"Status: {status}"
    )
    if voted:
        text += "\n\n✅ *You have already voted on this consultation.*"
    buttons = [
        [InlineKeyboardButton("📖 Learn More", callback_data=f"know|{c['id']}")],
    ]
    if not voted:
        buttons.append([
            InlineKeyboardButton("✅ Support", callback_data=f"vote|{c['id']}|support"),
            InlineKeyboardButton("❌ Oppose", callback_data=f"vote|{c['id']}|oppose"),
        ])
        buttons.append([InlineKeyboardButton("💬 Share My View", callback_data=f"opinion|{c['id']}")])
    buttons.append([InlineKeyboardButton("📊 See Results", callback_data=f"results|{c['id']}")])
    return text, InlineKeyboardMarkup(buttons)


def _eu_result_card() -> tuple[str, InlineKeyboardMarkup]:
    c = EU_RESULT
    text = (
        f"{c['level_emoji']} *{c['level']} Consultation — CLOSED*\n"
        f"*{c['title']}*\n\n"
        f"{c['summary']}\n\n"
        f"📅 {c['deadline']}\n\n"
        f"{c['result']}"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔁 Back to Main Menu", callback_data="start")
    ]])
    return text, kb


# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    await update.message.reply_text(
        f"👋 Welcome to *EU CivicConnect*, {user.first_name}!\n\n"
        "This platform lets you participate in real public consultations — "
        "at municipal, national, and European levels.\n\n"
        "Below you'll find two open consultations. Vote, share your view, "
        "and discover what other citizens think. 🗳️",
        parse_mode="Markdown",
    )
    for cid, c in CONSULTATIONS.items():
        voted = has_voted(uid, cid)
        text, kb = _consultation_card(c, voted=voted)
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)

    if has_voted_all(uid, CONSULTATION_IDS):
        text, kb = _eu_result_card()
        await update.message.reply_text(
            "🎉 You've participated in both consultations! Here's a recently closed EU result:",
            parse_mode="Markdown",
        )
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = ["📊 *Current Vote Counts*\n"]
    total = get_total_participants()
    lines.append(f"👥 Total participants: {total}\n")
    for cid, c in CONSULTATIONS.items():
        counts = get_vote_counts(cid)
        support = counts.get("support", 0)
        oppose = counts.get("oppose", 0)
        total_votes = support + oppose
        if total_votes > 0:
            pct = int(support / total_votes * 100)
            lines.append(
                f"{c['level_emoji']} *{c['title']}*\n"
                f"  ✅ Support: {support} ({pct}%) | ❌ Oppose: {oppose} ({100-pct}%)\n"
            )
        else:
            lines.append(f"{c['level_emoji']} *{c['title']}*\n  No votes yet.\n")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def button_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    data = query.data

    if data == "start":
        await query.message.reply_text("Use /start to see the main menu.")
        return

    parts = data.split("|")
    action = parts[0]

    if action == "know":
        cid = parts[1]
        c = CONSULTATIONS.get(cid)
        if not c:
            return
        voted = has_voted(uid, cid)
        text, kb = _consultation_card(c, voted=voted)
        detail_text = f"📋 *Details: {c['title']}*\n\n{c['detail']}"
        await query.message.reply_text(detail_text, parse_mode="Markdown", reply_markup=kb)

    elif action == "vote":
        cid, vote = parts[1], parts[2]
        c = CONSULTATIONS.get(cid)
        if not c:
            return
        recorded = record_vote(uid, cid, vote)
        label = "✅ Support" if vote == "support" else "❌ Oppose"
        if recorded:
            await query.edit_message_text(
                f"{c['level_emoji']} *{c['title']}*\n\n"
                f"Your vote has been recorded: *{label}*\n\n"
                "Thank you for participating! 🙏",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💬 Share Why", callback_data=f"opinion|{cid}"),
                    InlineKeyboardButton("📊 Results", callback_data=f"results|{cid}"),
                ]]),
            )
            if has_voted_all(uid, CONSULTATION_IDS):
                text, kb = _eu_result_card()
                await query.message.reply_text(
                    "🎉 You've now participated in both consultations! Here's a recently closed EU result:",
                    parse_mode="Markdown",
                )
                await query.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)
        else:
            await query.answer("You've already voted on this consultation.", show_alert=True)

    elif action == "opinion":
        cid = parts[1]
        c = CONSULTATIONS.get(cid)
        if not c:
            return
        _awaiting_opinion[uid] = cid
        await query.message.reply_text(
            f"💬 *Share your view on:*\n_{c['title']}_\n\n"
            "Please type your message and send it. Your input will be acknowledged.",
            parse_mode="Markdown",
        )

    elif action == "results":
        cid = parts[1]
        c = CONSULTATIONS.get(cid)
        if not c:
            return
        counts = get_vote_counts(cid)
        support = counts.get("support", 0)
        oppose = counts.get("oppose", 0)
        total = support + oppose
        if total == 0:
            text = f"📊 *{c['title']}*\n\nNo votes recorded yet. Be the first to vote!"
        else:
            pct_s = int(support / total * 100)
            bar_s = "█" * (pct_s // 5) + "░" * (20 - pct_s // 5)
            bar_o = "█" * ((100 - pct_s) // 5) + "░" * (20 - (100 - pct_s) // 5)
            text = (
                f"📊 *{c['title']}*\n\n"
                f"✅ Support: {support} votes ({pct_s}%)\n`{bar_s}`\n"
                f"❌ Oppose: {oppose} votes ({100-pct_s}%)\n`{bar_o}`\n\n"
                f"👥 Total votes: {total}"
            )
        await query.message.reply_text(text, parse_mode="Markdown")


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    if uid in _awaiting_opinion:
        cid = _awaiting_opinion.pop(uid)
        c = CONSULTATIONS.get(cid, {})
        record_opinion(uid, cid, text)
        context_hint = f"{c.get('title', '')} — {c.get('summary', '')[:200]}"
        reply = get_reply(text, context=context_hint)
        await update.message.reply_text(
            f"💬 *Your view has been noted. Thank you!*\n\n{reply}",
            parse_mode="Markdown",
        )
    else:
        reply = get_reply(text)
        await update.message.reply_text(reply, parse_mode="Markdown")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    init_db()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("Starting webhook on port 8100 at /telegram")
    application.run_webhook(
        listen="0.0.0.0",
        port=8100,
        url_path="telegram",
        webhook_url=f"https://{DOMAIN}/telegram",
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
