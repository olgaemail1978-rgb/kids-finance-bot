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
from ai_advisor import get_financial_advice, chat_with_advisor

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

EXPENSE_CATEGORIES = ["Еда", "Игрушки", "Книги", "Транспорт", "Одежда", "Развлечения", "Другое"]

# Main keyboard
def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 Мой баланс"), KeyboardButton("📊 История")],
        [KeyboardButton("➕ Добавить доход"), KeyboardButton("➖ Добавить расход")],
        [KeyboardButton("🎯 Мои цели"), KeyboardButton("🤖 Совет AI")]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Привет, {CHILD_NAME}! 👋\n\n"
        f"Я твой личный финансовый помощник. Буду помогать тебе следить за деньгами и копить на мечты! 💫\n\n"
        f"Что хочешь сделать? Можешь нажать кнопку или просто написать мне вопрос — я отвечу! 🤖",
        reply_markup=main_keyboard()
    )
    return CHOOSING_ACTION

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = get_balance(CHILD_NAME)
    emoji = "😊" if balance >= 0 else "😟"
    await update.message.reply_text(
        f"{emoji} Твой баланс: *{balance:.2f} руб.*",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    return CHOOSING_ACTION

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    transactions = get_transactions(CHILD_NAME, limit=10)
    if not transactions:
        await update.message.reply_text(
            "📭 Транзакций пока нет. Добавь первый доход!",
            reply_markup=main_keyboard()
        )
        return CHOOSING_ACTION
    lines = ["📊 *Последние 10 транзакций:*\n"]
    for tx in transactions:
        sign = "+" if tx["amount"] > 0 else ""
        emoji = "📈" if tx["amount"] > 0 else "📉"
        lines.append(f"{emoji} {tx['date']}: {sign}{tx['amount']:.0f} руб. — {tx['category']}: {tx['description']}")
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    return CHOOSING_ACTION

async def start_add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💵 Сколько денег ты получил? Введи сумму (например: 100):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True)
    )
    return ADDING_INCOME_AMOUNT

async def add_income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    try:
        amount = float(update.message.text.replace(",", "."))
        context.user_data["income_amount"] = amount
        await update.message.reply_text(
            "📝 Откуда эти деньги? Напиши описание (например: карманные деньги, подарок):",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Карманные деньги"), KeyboardButton("Подарок")],
                                              [KeyboardButton("Отмена")]], resize_keyboard=True)
        )
        return ADDING_INCOME_DESC
    except ValueError:
        await update.message.reply_text("❌ Это не похоже на число. Попробуй ещё раз:")
        return ADDING_INCOME_AMOUNT

async def add_income_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    amount = context.user_data.get("income_amount", 0)
    description = update.message.text
    success, error_msg = add_transaction(amount, "Доход", description, CHILD_NAME)
    if success:
        balance = get_balance(CHILD_NAME)
        await update.message.reply_text(
            f"✅ Записано! +{amount:.0f} руб. — {description}\n💰 Новый баланс: *{balance:.2f} руб.*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    else:
        logger.error(f"add_income_desc failed: {error_msg}")
        await update.message.reply_text(
            f"❌ Ошибка при сохранении: {error_msg}\nПопробуй ещё раз.",
            reply_markup=main_keyboard()
        )
    return CHOOSING_ACTION

async def start_add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💸 Сколько ты потратил? Введи сумму:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True)
    )
    return ADDING_EXPENSE_AMOUNT

async def add_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    try:
        amount = float(update.message.text.replace(",", "."))
        context.user_data["expense_amount"] = amount
        cat_buttons = [[KeyboardButton(c)] for c in EXPENSE_CATEGORIES]
        cat_buttons.append([KeyboardButton("Отмена")])
        await update.message.reply_text(
            "🗂️ Выбери категорию:",
            reply_markup=ReplyKeyboardMarkup(cat_buttons, resize_keyboard=True)
        )
        return ADDING_EXPENSE_CATEGORY
    except ValueError:
        await update.message.reply_text("❌ Это не похоже на число. Попробуй ещё раз:")
        return ADDING_EXPENSE_AMOUNT

async def add_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    category = update.message.text
    if category not in EXPENSE_CATEGORIES:
        category = "Другое"
    context.user_data["expense_category"] = category
    await update.message.reply_text(
        "📝 Напиши, на что потратил (например: мороженое, книга про динозавров):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True)
    )
    return ADDING_EXPENSE_DESC

async def add_expense_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    amount = context.user_data.get("expense_amount", 0)
    category = context.user_data.get("expense_category", "Другое")
    description = update.message.text
    success, error_msg = add_transaction(-amount, category, description, CHILD_NAME)
    if success:
        balance = get_balance(CHILD_NAME)
        await update.message.reply_text(
            f"✅ Записано! -{amount:.0f} руб. — {category}: {description}\n💰 Новый баланс: *{balance:.2f} руб.*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    else:
        logger.error(f"add_expense_desc failed: {error_msg}")
        await update.message.reply_text(
            f"❌ Ошибка при сохранении: {error_msg}\nПопробуй ещё раз.",
            reply_markup=main_keyboard()
        )
    return CHOOSING_ACTION

async def show_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goals = get_goals(CHILD_NAME)
    keyboard = [
        [KeyboardButton("🎯 Добавить цель"), KeyboardButton("💰 Пополнить цель")],
        [KeyboardButton("🔙 Назад")]
    ]
    if not goals:
        await update.message.reply_text(
            "🎯 У тебя пока нет целей накопления.\n\nПоставь цель — и начни копить на мечту!",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
    else:
        lines = ["🎯 *Твои цели:*\n"]
        for g in goals:
            bar_filled = int(g["percent"] / 10)
            bar = "🟩" * bar_filled + "⬜" * (10 - bar_filled)
            lines.append(f"*{g['name']}*\n{bar} {g['percent']}%\nНакоплено: {g['saved']:.0f} / {g['target']:.0f} руб.\n")
        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
    return CHOOSING_ACTION

async def start_add_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 Как называется твоя цель? (например: велосипед, телефон, поездка)",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True)
    )
    return ADDING_GOAL_NAME

async def add_goal_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    context.user_data["goal_name"] = update.message.text
    await update.message.reply_text(
        "💰 Сколько нужно накопить? Введи сумму:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True)
    )
    return ADDING_GOAL_AMOUNT

async def add_goal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    try:
        target = float(update.message.text.replace(",", "."))
        goal_name = context.user_data.get("goal_name", "Цель")
        success, error_msg = add_goal(CHILD_NAME, goal_name, target)
        if success:
            await update.message.reply_text(
                f"✅ Цель создана: *{goal_name}* — {target:.0f} руб.\n\nНачинай копить! 🚀",
                parse_mode="Markdown",
                reply_markup=main_keyboard()
            )
        else:
            logger.error(f"add_goal_amount failed: {error_msg}")
            await update.message.reply_text(
                f"❌ Ошибка при создании цели: {error_msg}",
                reply_markup=main_keyboard()
            )
    except ValueError:
        await update.message.reply_text("❌ Это не похоже на число. Попробуй ещё раз:")
        return ADDING_GOAL_AMOUNT
    return CHOOSING_ACTION

async def start_save_for_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goals = get_goals(CHILD_NAME)
    if not goals:
        await update.message.reply_text(
            "🎯 У тебя пока нет целей. Сначала создай цель!",
            reply_markup=main_keyboard()
        )
        return CHOOSING_ACTION
    goal_buttons = [[KeyboardButton(g["name"])] for g in goals]
    goal_buttons.append([KeyboardButton("Отмена")])
    await update.message.reply_text(
        "🎯 Выбери цель, на которую хочешь отложить деньги:",
        reply_markup=ReplyKeyboardMarkup(goal_buttons, resize_keyboard=True)
    )
    context.user_data["goals_list"] = goals
    return SAVING_FOR_GOAL_SELECT

async def select_goal_to_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    goals = context.user_data.get("goals_list", [])
    goal_name = update.message.text
    goal = next((g for g in goals if g["name"] == goal_name), None)
    if not goal:
        await update.message.reply_text("❌ Цель не найдена. Попробуй ещё раз.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    context.user_data["selected_goal"] = goal
    await update.message.reply_text(
        f"💰 Сколько откладываешь на «{goal_name}»? Введи сумму:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True)
    )
    return SAVING_FOR_GOAL_AMOUNT

async def add_goal_savings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    try:
        amount = float(update.message.text.replace(",", "."))
        goal = context.user_data.get("selected_goal", {})
        goal_name = goal.get("name", "Цель")
        goal_id = goal.get("id", "")
        success, error_msg = update_goal_saved(goal_id, amount)
        if success:
            add_transaction(-amount, "Копилка", f"Пополнение цели: {goal_name}", CHILD_NAME)
            await update.message.reply_text(
                f"✅ Отложено {amount:.0f} руб. на «{goal_name}»! 🎯",
                reply_markup=main_keyboard()
            )
        else:
            logger.error(f"add_goal_savings failed: {error_msg}")
            await update.message.reply_text(
                f"❌ Ошибка при обновлении цели: {error_msg}",
                reply_markup=main_keyboard()
            )
    except ValueError:
        await update.message.reply_text("❌ Это не похоже на число. Попробуй ещё раз:")
        return SAVING_FOR_GOAL_AMOUNT
    return CHOOSING_ACTION

async def get_ai_advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Анализирую твои финансы...", reply_markup=main_keyboard())
    balance = get_balance(CHILD_NAME)
    transactions = get_transactions(CHILD_NAME)
    goals = get_goals(CHILD_NAME)
    advice = get_financial_advice(CHILD_NAME, balance, transactions, goals)
    await update.message.reply_text(
        f"🤖 *Совет от AI-советника:*\n\n{advice}",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    return CHOOSING_ACTION

async def handle_free_text_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any free-text message as a question to the AI advisor."""
    question = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        balance = get_balance(CHILD_NAME)
        transactions = get_transactions(CHILD_NAME, limit=5)
        goals = get_goals(CHILD_NAME)
        response = chat_with_advisor(CHILD_NAME, question, balance, transactions, goals)
        await update.message.reply_text(
            f"🤖 {response}",
            reply_markup=main_keyboard()
        )
    except Exception as e:
        logger.error(f"Free text AI error: {e}")
        await update.message.reply_text(
            "🤖 Не могу ответить прямо сейчас. Попробуй кнопку «Совет AI»!",
            reply_markup=main_keyboard()
        )
    return CHOOSING_ACTION

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Главное меню:", reply_markup=main_keyboard())
    return CHOOSING_ACTION

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ACTION: [
                MessageHandler(filters.Regex("^💰 Мой баланс$"), show_balance),
                MessageHandler(filters.Regex("^📊 История$"), show_history),
                MessageHandler(filters.Regex("^➕ Добавить доход$"), start_add_income),
                MessageHandler(filters.Regex("^➖ Добавить расход$"), start_add_expense),
                MessageHandler(filters.Regex("^🎯 Мои цели$"), show_goals),
                MessageHandler(filters.Regex("^🤖 Совет AI$"), get_ai_advice),
                MessageHandler(filters.Regex("^🎯 Добавить цель$"), start_add_goal),
                MessageHandler(filters.Regex("^💰 Пополнить цель$"), start_save_for_goal),
                MessageHandler(filters.Regex("^🔙 Назад$"), handle_back),
                # Any free text → AI advisor (must be last!)
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_free_text_question),
            ],
            ADDING_INCOME_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_income_amount)],
            ADDING_INCOME_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_income_desc)],
            ADDING_EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_amount)],
            ADDING_EXPENSE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_category)],
            ADDING_EXPENSE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_desc)],
            ADDING_GOAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_goal_name)],
            ADDING_GOAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_goal_amount)],
            SAVING_FOR_GOAL_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_goal_to_save)],
            SAVING_FOR_GOAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_goal_savings)],
        },
        fallbacks=[
            CommandHandler("start", start),
        ],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    logger.info(f"Бот запущен для {CHILD_NAME}...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
