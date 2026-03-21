# -*- coding: utf-8 -*-
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from config import BOT_TOKEN, CHILD_NAME
from notion_db import (
    add_transaction, get_balance, get_transactions,
    add_goal, get_goals, update_goal_saved
)
from ai_advisor import get_financial_advice

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_ACTION = 0
ADDING_INCOME_AMOUNT = 1
ADDING_INCOME_DESC = 2
ADDING_EXPENSE_AMOUNT = 3
ADDING_EXPENSE_CATEGORY = 4
ADDING_EXPENSE_DESC = 5
ADDING_GOAL_NAME = 6
ADDING_GOAL_AMOUNT = 7
SAVING_FOR_GOAL_SELECT = 8
SAVING_FOR_GOAL_AMOUNT = 9

EXPENSE_CATEGORIES = ["Ãâ¢ÃÂ´ÃÂ°", "ÃËÃÂ³Ãâ¬ÃÆÃËÃÂºÃÂ¸", "ÃÅ¡ÃÂ½ÃÂ¸ÃÂ³ÃÂ¸", "ÃÂ¢Ãâ¬ÃÂ°ÃÂ½ÃÂÃÂ¿ÃÂ¾Ãâ¬Ãâ", "ÃÅ¾ÃÂ´ÃÂµÃÂ¶ÃÂ´ÃÂ°", "ÃÂ ÃÂ°ÃÂ·ÃÂ²ÃÂ»ÃÂµÃâ¡ÃÂµÃÂ½ÃÂ¸ÃÂ", "ÃâÃâ¬ÃÆÃÂ³ÃÂ¾ÃÂµ"]

# Main keyboard
def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("Ã°Å¸âÂ° ÃÅÃÂ¾ÃÂ¹ ÃÂ±ÃÂ°ÃÂ»ÃÂ°ÃÂ½ÃÂ"), KeyboardButton("Ã°Å¸âÅ  ÃËÃÂÃâÃÂ¾Ãâ¬ÃÂ¸ÃÂ")],
        [KeyboardButton("Ã¢Å¾â¢ ÃâÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃâÃÅ ÃÂ´ÃÂ¾Ãâ¦ÃÂ¾ÃÂ´"), KeyboardButton("Ã¢Å¾â ÃâÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃâÃÅ Ãâ¬ÃÂ°ÃÂÃâ¦ÃÂ¾ÃÂ´")],
        [KeyboardButton("Ã°Å¸Å½Â¯ ÃÅÃÂ¾ÃÂ¸ Ãâ ÃÂµÃÂ»ÃÂ¸"), KeyboardButton("Ã°Å¸Â¤â ÃÂ¡ÃÂ¾ÃÂ²ÃÂµÃâ AI")]
    ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"ÃÅ¸Ãâ¬ÃÂ¸ÃÂ²ÃÂµÃâ, {CHILD_NAME}! Ã°Å¸ââ¹\n\n"
        f"ÃÂ¯ ÃâÃÂ²ÃÂ¾ÃÂ¹ ÃÂ»ÃÂ¸Ãâ¡ÃÂ½Ãâ¹ÃÂ¹ ÃâÃÂ¸ÃÂ½ÃÂ°ÃÂ½ÃÂÃÂ¾ÃÂ²Ãâ¹ÃÂ¹ ÃÂ¿ÃÂ¾ÃÂ¼ÃÂ¾Ãâ°ÃÂ½ÃÂ¸ÃÂº. ÃâÃÆÃÂ´ÃÆ ÃÂ¿ÃÂ¾ÃÂ¼ÃÂ¾ÃÂ³ÃÂ°ÃâÃÅ ÃâÃÂµÃÂ±ÃÂµ ÃÂÃÂ»ÃÂµÃÂ´ÃÂ¸ÃâÃÅ ÃÂ·ÃÂ° ÃÂ´ÃÂµÃÂ½ÃÅÃÂ³ÃÂ°ÃÂ¼ÃÂ¸ ÃÂ¸ ÃÂºÃÂ¾ÃÂ¿ÃÂ¸ÃâÃÅ ÃÂ½ÃÂ° ÃÂ¼ÃÂµÃâ¡ÃâÃâ¹! Ã°Å¸âÂ«\n\n"
        f"ÃÂ§ÃâÃÂ¾ Ãâ¦ÃÂ¾Ãâ¡ÃÂµÃËÃÅ ÃÂÃÂ´ÃÂµÃÂ»ÃÂ°ÃâÃÅ?",
        reply_markup=main_keyboard()
    )
    return CHOOSING_ACTION


async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = get_balance(CHILD_NAME)
    emoji = "Ã°Å¸ËÅ " if balance >= 0 else "Ã°Å¸ËÅ¸"
    await update.message.reply_text(
        f"{emoji} ÃÂ¢ÃÂ²ÃÂ¾ÃÂ¹ ÃÂ±ÃÂ°ÃÂ»ÃÂ°ÃÂ½ÃÂ: *{balance:.2f} Ãâ¬ÃÆÃÂ±.*",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    return CHOOSING_ACTION


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    transactions = get_transactions(CHILD_NAME, limit=10)
    if not transactions:
        await update.message.reply_text(
            "Ã°Å¸âÂ­ ÃÂ¢Ãâ¬ÃÂ°ÃÂ½ÃÂ·ÃÂ°ÃÂºÃâ ÃÂ¸ÃÂ¹ ÃÂ¿ÃÂ¾ÃÂºÃÂ° ÃÂ½ÃÂµÃâ. ÃâÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÅ ÃÂ¿ÃÂµÃâ¬ÃÂ²Ãâ¹ÃÂ¹ ÃÂ´ÃÂ¾Ãâ¦ÃÂ¾ÃÂ´!",
            reply_markup=main_keyboard()
        )
        return CHOOSING_ACTION

    lines = ["Ã°Å¸âÅ  *ÃÅ¸ÃÂ¾ÃÂÃÂ»ÃÂµÃÂ´ÃÂ½ÃÂ¸ÃÂµ 10 ÃâÃâ¬ÃÂ°ÃÂ½ÃÂ·ÃÂ°ÃÂºÃâ ÃÂ¸ÃÂ¹:*\n"]
    for tx in transactions:
        sign = "+" if tx["amount"] > 0 else ""
        emoji = "Ã°Å¸âË" if tx["amount"] > 0 else "Ã°Å¸ââ°"
        lines.append(f"{emoji} {tx['date']}: {sign}{tx['amount']:.0f} Ãâ¬ÃÆÃÂ±. Ã¢â¬â {tx['category']}: {tx['description']}")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    return CHOOSING_ACTION


async def start_add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ã°Å¸âÂµ ÃÂ¡ÃÂºÃÂ¾ÃÂ»ÃÅÃÂºÃÂ¾ ÃÂ´ÃÂµÃÂ½ÃÂµÃÂ³ ÃâÃâ¹ ÃÂ¿ÃÂ¾ÃÂ»ÃÆÃâ¡ÃÂ¸ÃÂ»? ÃâÃÂ²ÃÂµÃÂ´ÃÂ¸ ÃÂÃÆÃÂ¼ÃÂ¼ÃÂµ (ÃÂ½ÃÂ°ÃÂ¿Ãâ¬ÃÂ¸ÃÂ¼ÃÂµÃâ¬: 100):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°")]], resize_keyboard=True)
    )
    return ADDING_INCOME_AMOUNT


async def add_income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°":
        await update.message.reply_text("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ½ÃÂ¾.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    try:
        amount = float(update.message.text.replace(",", "."))
        context.user_data["income_amount"] = amount
        await update.message.reply_text(
            "Ã°Å¸âÂ ÃÅ¾ÃâÃÂºÃÆÃÂ´ÃÂ° ÃÂÃâÃÂ¸ ÃÂ´ÃÂµÃÂ½ÃÅÃÂ³ÃÂ¸? ÃÂÃÂ°ÃÂ¿ÃÂ¸ÃËÃÂ¸ ÃÂ¾ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂµ (ÃÂ½ÃÂ°ÃÂ¿Ãâ¬ÃÂ¸ÃÂ¼ÃÂµÃâ¬: ÃÂºÃÂ°Ãâ¬ÃÂ¼ÃÂ°ÃÂ½ÃÂ½Ãâ¹ÃÂµ ÃÂ´ÃÂµÃÂ½ÃÅÃÂ³ÃÂ¸, ÃÂ¿ÃÂ¾ÃÂ´ÃÂ°Ãâ¬ÃÂ¾ÃÂº):",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("ÃÅ¡ÃÂ°Ãâ¬ÃÂ¼ÃÂ°ÃÂ½ÃÂ½Ãâ¹ÃÂµ ÃÂ´ÃÂµÃÂ½ÃÅÃÂ³ÃÂ¸"), KeyboardButton("ÃÅ¸ÃÂ¾ÃÂ´ÃÂ°Ãâ¬ÃÂ¾ÃÂº")], [KeyboardButton("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°")]], resize_keyboard=True)
        )
        return ADDING_INCOME_DESC
    except ValueError:
        await update.message.reply_text("Ã¢ÂÅ ÃÂ­ÃâÃÂ¾ ÃÂ½ÃÂµ ÃÂ¿ÃÂ¾Ãâ¦ÃÂ¾ÃÂ¶ÃÂµ ÃÂ½ÃÂ° Ãâ¡ÃÂ¸ÃÂÃÂ»ÃÂ¾. ÃÅ¸ÃÂ¾ÃÂ¿Ãâ¬ÃÂ¾ÃÂ±ÃÆÃÂ¹ ÃÂµÃâ°Ãâ Ãâ¬ÃÂ°ÃÂ·:")
        return ADDING_INCOME_AMOUNT


async def add_income_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°":
        await update.message.reply_text("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ½ÃÂ¾.", reply_markup=main_keyboard())
        return CHOOSING_ACTION

    amount = context.user_data.get("income_amount", 0)
    description = update.message.text

    success = add_transaction(amount, "ÃâÃÂ¾Ãâ¦ÃÂ¾ÃÂ´", description, CHILD_NAME)
    if success:
        balance = get_balance(CHILD_NAME)
        await update.message.reply_text(
            f"Ã¢Åâ¦ ÃâÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂ½ÃÂ¾! +{amount:.0f} Ãâ¬ÃÆÃÂ±. Ã¢â¬â {description}\nÃ°Å¸âÂ° ÃÂÃÂ¾ÃÂ²Ãâ¹ÃÂ¹ ÃÂ±ÃÂ°ÃÂ»ÃÂ°ÃÂ½ÃÂ: *{balance:.2f} Ãâ¬ÃÆÃÂ±.*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    else:
        await update.message.reply_text("Ã¢ÂÅ ÃÅ¾ÃËÃÂ¸ÃÂ±ÃÂºÃÂ° ÃÂ¿Ãâ¬ÃÂ¸ ÃÂÃÂ¾Ãâ¦Ãâ¬ÃÂ°ÃÂ½ÃÂµÃÂ½ÃÂ¸ÃÂ¸. ÃÅ¸ÃÂ¾ÃÂ¿Ãâ¬ÃÂ¾ÃÂ±ÃÆÃÂ¹ ÃÂµÃâ°Ãâ Ãâ¬ÃÂ°ÃÂ·.", reply_markup=main_keyboard())
    return CHOOSING_ACTION


async def start_add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ã°Å¸âÂ¸ ÃÂ¡ÃÂºÃÂ¾ÃÂ»ÃÅÃÂºÃÂ¾ ÃâÃâ¹ ÃÂ¿ÃÂ¾ÃâÃâ¬ÃÂ°ÃâÃÂ¸ÃÂ»? ÃâÃÂ²ÃÂµÃÂ´ÃÂ¸ ÃÂÃÆÃÂ¼ÃÂ¼ÃÆ:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°")]], resize_keyboard=True)
    )
    return ADDING_EXPENSE_AMOUNT


async def add_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°":
        await update.message.reply_text("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ½ÃÂ¾.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    try:
        amount = float(update.message.text.replace(",", "."))
        context.user_data["expense_amount"] = amount

        cat_buttons = [[KeyboardButton(c)] for c in EXPENSE_CATEGORIES]
        cat_buttons.append([KeyboardButton("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°")])

        await update.message.reply_text(
            "Ã°Å¸ÂÂ·Ã¯Â¸Â ÃâÃâ¹ÃÂ±ÃÂµÃâ¬ÃÂ¸ ÃÂºÃÂ°ÃâÃÂµÃÂ³ÃÂ¾Ãâ¬ÃÂ¸ÃÅ½:",
            reply_markup=ReplyKeyboardMarkup(cat_buttons, resize_keyboard=True)
        )
        return ADDING_EXPENSE_CATEGORY
    except ValueError:
        await update.message.reply_text("Ã¢ÂÅ ÃÂ­ÃâÃÂ¾ ÃÂ½ÃÂµ ÃÂ¿ÃÂ¾Ãâ¦ÃÂ¾ÃÂ¶ÃÂµ ÃÂ½ÃÂ° Ãâ¡ÃÂ¸ÃÂÃÂ»ÃÂ¾. ÃÅ¸ÃÂ¾ÃÂ¿Ãâ¬ÃÂ¾ÃÂ±ÃÆÃÂ¹ ÃÂµÃâ°Ãâ Ãâ¬ÃÂ°Ãw:")
        return ADDING_EXPENSE_AMOUNT


async def add_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°":
        await update.message.reply_text("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ½ÃÂ¾.", reply_markup=main_keyboard())
        return CHOOSING_ACTION

    category = update.message.text
    if category not in EXPENSE_CATEGORIES:
        category = "ÃâÃâ¬ÃÆÃÂ³ÃÂ¾ÃÂµ"
    context.user_data["expense_category"] = category

    await update.message.reply_text(
        "Ã°Å¸âÂ ÃÂÃÂ°ÃÂ¿ÃÂ¸ÃËÃÂ¸, ÃÂ½ÃÂ° Ãâ¡ÃâÃÂ¾ ÃÂ¿ÃÂ¾ÃâÃâ¬ÃÂ°ÃâÃÂ¸ÃÂ» (ÃÂ½ÃÂ°ÃÂ¿Ãâ¬ÃÂ¸ÃÂ¼ÃÂµÃâ¬: ÃÂ¼ÃÂ¾Ãâ¬ÃÂ¾ÃÂ¶ÃÂµÃÂ½ÃÂ¾ÃÂµ, ÃÂºÃÂ½ÃÂ¸ÃÂ³ÃÂ° ÃÂ¿Ãâ¬ÃÂ¾ ÃÂ´ÃÂ¸ÃÂ½ÃÂ¾ÃÂ·ÃÂ°ÃÂ²Ãâ¬ÃÂ¾ÃÂ²):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°")]], resize_keyboard=True)
    )
    return ADDING_EXPENSE_DESC


async def add_expense_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°":
        await update.message.reply_text("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ½ÃÂ¾.", reply_markup=main_keyboard())
        return CHOOSING_ACTION

    amount = context.user_data.get("expense_amount", 0)
    category = context.user_data.get("expense_category", "ÃâÃâ¬ÃÆÃÂ³ÃÂ¾ÃÂµ")
    description = update.message.text

    success = add_transaction(-amount, category, description, CHILD_NAME)
    if success:
        balance = get_balance(CHILD_NAME)
        await update.message.reply_text(
            f"Ã¢Åâ¦ ÃâÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂ½ÃÂ¾! -{amount:.0f} Ãâ¬ÃÆÃÂ±. Ã¢â¬â {category}: {description}\nÃ°Å¸âÂ° ÃÂÃÂ¾ÃÂ²Ãâ¹ÃÂ¹ ÃÂ±ÃÂ°ÃÂ»ÃÂ°ÃÂ½ÃÂ: *{balance:.2f} Ãâ¬ÃÆÃÂ±.*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    else:
        await update.message.reply_text("Ã¢ÂÅ ÃÅ¾ÃËÃÂ¸ÃÂ±ÃÂºÃÂ° ÃÂ¿Ãâ¬ÃÂ¸ ÃÂÃÂ¾Ãâ¦Ãâ¬ÃÂ°ÃÂ½ÃÂµÃÂ½ÃÂ¸ÃÂ¸. ÃÅ¸ÃÂ¾ÃÂ¿Ãâ¬ÃÂ¾ÃÂ±ÃÆÃÂ¹ ÃÂµÃâ°Ãâ Ãâ¬ÃÂ°ÃÂ·.", reply_markup=main_keyboard())
    return CHOOSING_ACTION


async def show_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goals = get_goals(CHILD_NAME)

    keyboard = [
        [KeyboardButton("Ã°Å¸Å½Â¯ ÃâÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃâÃÅ Ãâ ÃÂµÃÂ»ÃÅ"), KeyboardButton("Ã°Å¸âÂ° ÃÅ¸ÃÂ¾ÃÂ¿ÃÂ¾ÃÂ»ÃÂ½ÃÂ¸ÃâÃÅ Ãâ ÃÂµÃÂ»ÃÅ")],
        [KeyboardButton("Ã°Å¸ââ¢ ÃÂÃÂ°ÃÂ·ÃÂ°ÃÂ´")]
    ]

    if not goals:
        await update.message.reply_text(
            "Ã°Å¸Å½Â¯ ÃÂ£ ÃâÃÂµÃÂ±ÃÂ ÃÂ¿ÃÂ¾ÃÂºÃÂ° ÃÂ½ÃÂµÃâ Ãâ ÃÂµÃÂ»ÃÂµÃÂ¹ ÃÂ½ÃÂ°ÃÂºÃÂ¾ÃÂ¿ÃÂ»ÃÂµÃÂ½ÃÂ¸ÃÂ.\n\nÃÅ¸ÃÂ¾ÃÂÃâÃÂ°ÃÂ²ÃÅ Ãâ ÃÂµÃÂ»ÃÅ Ã¢â¬â ÃÂ¸ ÃÂ½ÃÂ°Ãâ¡ÃÂ½ÃÂ¸ ÃÂºÃÂ¾ÃÂ¿ÃÂ¸ÃâÃÅ ÃÂ½ÃÂ° ÃÂ¼ÃÂµÃâ¡ÃâÃÆ!",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
    else:
        lines = ["Ã°Å¸Å½Â¯ *ÃÂ¢ÃÂ²ÃÂ¾ÃÂ¸ Ãâ ÃÂµÃÂ»ÃÂ¸:*\n"]
        for g in goals:
            bar_filled = int(g["percent"] / 10)
            bar = "Ã°Å¸Å¸Â©" * bar_filled + "Ã¢Â¬Å" * (10 - bar_filled)
            lines.append(f"*{g['name']}*\n{bar} {g['percent']}%\nÃÂÃÂ°ÃÂºÃÂ¾ÃÂ¿ÃÂ»ÃÂµÃÂ½ÃÂ¾: {g['saved']:.0f} / {g['target']:.0f} Ãâ¬ÃÆÃÂ±.\n")

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
    return CHOOSING_ACTION


async def start_add_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ã°Å¸Å½Â¯ ÃÅ¡ÃÂ°ÃÂº ÃÂ½ÃÂ°ÃÂ·Ãâ¹ÃÂ²ÃÂ°ÃÂµÃâÃÂÃÂ ÃâÃÂ²ÃÂ¾ÃÂ Ãâ ÃÂµÃÂ»ÃÅ? (ÃÂ½ÃÂ°ÃÂ¿Ãâ¬ÃÂ¸ÃÂ¼ÃÂµÃâ¬: ÃÂ²ÃÂµÃÂ»ÃÂ¾ÃÂÃÂ¸ÃÂ¿ÃÂµÃÂ´, ÃâÃÂµÃÂ»ÃÂµÃâÃÂ¾ÃÂ½, ÃÂ¿ÃÂ¾ÃÂµÃÂ·ÃÂ´ÃÂºÃÂ°)",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°")]], resize_keyboard=True)
    )
    return ADDING_GOAL_NAME


async def add_goal_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°":
        await update.message.reply_text("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ½ÃÂ¾.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    context.user_data["goal_name"] = update.message.text
    await update.message.reply_text(
        "Ã°Å¸âÂ° ÃÂ¡ÃÂºÃÂ¾ÃÂ»ÃÅÃÂºÃÂ¾ ÃÂ½ÃÆÃÂ¶ÃÂ½ÃÂ¾ ÃÂ½ÃÂ°ÃÂºÃÂ¾ÃÂ¿ÃÂ¸ÃâÃÅ? ÃâÃÂ²ÃÂµÃÂ´ÃÂ¸ ÃÂÃÆÃÂ¼ÃÂ¼ÃÆ:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°")]], resize_keyboard=True)
    )
    return ADDING_GOAL_AMOUNT


async def add_goal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂ°":
        await update.message.reply_text("ÃÅ¾ÃâÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ½ÃÂ¾.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    try:
        target = float(update.message.text.replace(",", "."))
        goal_name = context.user_data.get("goal_name", "ÃÂ¦ÃÂµÃÂ»ÃÅ")

        success = add_goal(CHILD_NAME, goal_name, target)
        if success:
            await update.message.reply_text(
                f"Ã¢Åâ¦ ÃÂ¦ÃÂµÃÂ»ÃÅ ÃÂÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂ½ÃÂ°: *{goal_name}* Ã¢â¬â {target:.0f} Ãâ¬ÃÆÃÂ±.\n\nÃÂÃÂ°Ãâ¡ÃÂ¸ÃÂ½ÃÂ°ÃÂ¹ ÃÂºÃÂ¾ÃÂ¿ÃÂ¸ÃâÃÅ! Ã°Å¸âÂª",
                parse_mode="Markdown",
                reply_markup=main_keyboard()
            )
        else:
            await update.message.reply_text("Ã¢ÂÅ ÃÅ¾ÃËÃÂ¸ÃÂ±ÃÂºÃÂ° ÃÂ¿Ãâ¬ÃÂ¸ ÃÂÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂ½ÃÂ¸ÃÂ¸ Ãâ ÃÂµÃÂ»ÃÂ¸.", reply_markup=main_keyboard())
    except ValueError:
        await update.message.reply_text("Ã¢ÂÅ ÃÂ­ÃâÃÂ¾ ÃÂ½ÃÂµ ÃÂ¿ÃÂ¾Ãâ¦ÃÂ¾ÃÂ¶ÃÂµ ÃÂ½ÃÂ° Ãâ¡ÃÂ¸ÃÂÃÂ»ÃÂ¾. ÃÅ¸ÃÂ¾ÃÂ¿Ãâ¬ÃÂ¾ÃÂ±ÃÆÃÂ¹ ÃÂµÃâ°Ãâ Ãâ¬ÃÂ°ÃÂ·:")
        return ADDING_GOAL_AMOUNT
    return CHOOSING_ACTION


async def get_ai_advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ã°Å¸Â¤â ÃÂÃÂ½ÃÂ°ÃÂ»ÃÂ¸ÃÂ·ÃÂ¸Ãâ¬ÃÆÃÅ½ ÃâÃÂ²ÃÂ¾ÃÂ¸ ÃâÃÂ¸ÃÂ½ÃÂ°ÃÂ½ÃÂÃâ¹...", reply_markup=main_keyboard())

    balance = get_balance(CHILD_NAME)
    transactions = get_transactions(CHILD_NAME)
    goals = get_goals(CHILD_NAME)

    advice = get_financial_advice(CHILD_NAME, balance, transactions, goals)

    await update.message.reply_text(
        f"Ã°Å¸Â¤â *ÃÂ¡ÃÂ¾ÃÂ²ÃÂµÃâ ÃÂ¾Ãâ AI-ÃÂÃÂ¾ÃÂ²ÃÂµÃâÃÂ½ÃÂ¸ÃÂºÃÂ°:*\n\n{advice}",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    return CHOOSING_ACTION


async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ÃâÃÂ»ÃÂ°ÃÂ²ÃÂ½ÃÂ¾ÃÂµ ÃÂ¼ÃÂµÃÂ½ÃÅ½:", reply_markup=main_keyboard())
    return CHOOSING_ACTION


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ÃÂÃÂµ ÃÂ¿ÃÂ¾ÃÂ½ÃÂ¸ÃÂ¼ÃÂ°ÃÅ½ Ã°Å¸Â¤â ÃËÃÂÃÂ¿ÃÂ¾ÃÂ»ÃÅÃÂ·ÃÆÃÂ¹ ÃÂºÃÂ½ÃÂ¾ÃÂ¿ÃÂºÃÂ¸ ÃÂ¼ÃÂµÃÂ½ÃÅ½.",
        reply_markup=main_keyboard()
    )
    return CHOOSING_ACTION


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ACTION: [
                MessageHandler(filters.Regex("^Ã°Å¸âÂ° ÃÅÃÂ¾ÃÂ¹ ÃÂ±ÃÂ°ÃÂ»ÃÂ°ÃÂ½ÃÂ$"), show_balance),
                MessageHandler(filters.Regex("^Ã°Å¸âÅ  ÃËÃÂÃâÃÂ¾Ãâ¬ÃÂ¸ÃÂ$"), show_history),
                MessageHandler(filters.Regex("^Ã¢Å¾â¢ ÃâÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃâÃÅ ÃÂ´ÃÂ¾Ãâ¦ÃÂ¾ÃÂ´$"), start_add_income),
                MessageHandler(filters.Regex("^Ã¢Å¾â ÃâÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃâÃÅ Ãâ¬ÃÂ°ÃÂÃâ¦ÃÂ¾ÃÂ´$"), start_add_expense),
                MessageHandler(filters.Regex("^Ã°Å¸Å½Â¯ ÃÅÃÂ¾ÃÂ¸ Ãâ ÃÂµÃÂ»ÃÂ¸$"), show_goals),
                MessageHandler(filters.Regex("^Ã°Å¸Â¤â ÃÂ¡ÃÂ¾ÃÂ²ÃÂµÃâ AI$"), get_ai_advice),
                MessageHandler(filters.Regex("^Ã°Å¸Å½Â¯ ÃâÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃâÃÅ Ãâ ÃÂµÃÂ»ÃÅ$"), start_add_goal),
                MessageHandler(filters.Regex("^Ã°Å¸ââ¢ ÃÂÃÂ°ÃÂ·ÃÂ°ÃÂ´$"), handle_back),
            ],
            ADDING_INCOME_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_income_amount)],
            ADDING_INCOME_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_income_desc)],
            ADDING_EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_amount)],
            ADDING_EXPENSE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_category)],
            ADDING_EXPENSE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_desc)],
            ADDING_GOAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_goal_name)],
            ADDING_GOAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_goal_amount)],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT, unknown)
        ],
        allow_reentry=True
    )

    app.add_handler(conv_handler)

    logger.info(f"ÃâÃÂ¾Ãâ ÃÂ·ÃÂ°ÃÂ¿ÃÆÃâ°ÃÂµÃÂ½ ÃÂ´ÃÂ»ÃÂ {CHILD_NAME}...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
