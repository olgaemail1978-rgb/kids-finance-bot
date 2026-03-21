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

def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 Мой баланс"), KeyboardButton("📊 История")],
        [KeyboardButton("➕ Добавить доход"), KeyboardButton("➖ Добавить расход")],
        [KeyboardButton("🎯 Мои цели"), KeyboardButton("🤖 Совет AI")]
    ], resize_keyboard=True)

async def start(update, context):
    await update.message.reply_text(
        f"Привет, {CHILD_NAME}! 👋\n\nЯ твой личный финансовый помощник. Буду помогать тебе следить за деньгами и копить на мечты! 💫\n\nЧто хочешь сделать?",
        reply_markup=main_keyboard()
    )
    return CHOOSING_ACTION

async def show_balance(update, context):
    balance = get_balance(CHILD_NAME)
    emoji = "😊" if balance >= 0 else "😟"
    await update.message.reply_text(f"{emoji} Твой баланс: *{balance:.2f} руб.*", parse_mode="Markdown", reply_markup=main_keyboard())
    return CHOOSING_ACTION

async def show_history(update, context):
    transactions = get_transactions(CHILD_NAME, limit=10)
    if not transactions:
        await update.message.reply_text("📭 Транзакций пока нет. Добавь первый доход!", reply_markup=main_keyboard())
        return CHOOSING_ACTION
    lines = ["📊 *Последние 10 транзакций:*\n"]
    for tx in transactions:
        sign = "+" if tx["amount"] > 0 else ""
        emoji = "📈" if tx["amount"] > 0 else "📉"
        lines.append(f"{emoji} {tx['date']}: {sign}{tx['amount']:.0f} руб. — {tx['category']}: {tx['description']}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=main_keyboard())
    return CHOOSING_ACTION

async def start_add_income(update, context):
    await update.message.reply_text("💵 Сколько денег ты получил? Введи сумму (например: 100):", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True))
    return ADDING_INCOME_AMOUNT

async def add_income_amount(update, context):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard()); return CHOOSING_ACTION
    try:
        amount = float(update.message.text.replace(",","."))
        context.user_data["income_amount"] = amount
        await update.message.reply_text("📝 Откуда эти деньги? Напиши описание:", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Карманные деньги"), KeyboardButton("Подарок")],[KeyboardButton("Отмена")]], resize_keyboard=True))
        return ADDING_INCOME_DESC
    except ValueError:
        await update.message.reply_text("❌ Твой баланс не похоже на число. Попробуй ещё раз:"); return ADDING_INCOME_AMOUNT

async def add_income_desc(update, context):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard()); return CHOOSING_ACTION
    amount = context.user_data.get("income_amount", 0)
    success = add_transaction(amount, "Доход", update.message.text, CHILD_NAME)
    if success:
        balance = get_balance(CHILD_NAME)
        await update.message.reply_text(f"✅ +{amount:.0f} руб. записано!\n💰 Баланс: *{balance:.2f} руб.*", parse_mode="Markdown", reply_markup=main_keyboard())
    else:
        await update.message.reply_text("❌ Ошибка сохранения.", reply_markup=main_keyboard())
    return CHOOSING_ACTION

async def start_add_expense(update, context):
    await update.message.reply_text("💸 Сколько ты потратил? Введи сумму:", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True))
    return ADDING_EXPENSE_AMOUNT

async def add_expense_amount(update, context):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard()); return CHOOSING_ACTION
    try:
        amount = float(update.message.text.replace(",","."))
        context.user_data["expense_amount"] = amount
        cat_buttons = [[KeyboardButton(c)] for c in EXPENSE_CATEGORIES] + [[KeyboardButton("Отмена")]]
        await update.message.reply_text("🗂️ Выбери категорию:", reply_markup=ReplyKeyboardMarkup(cat_buttons, resize_keyboard=True))
        return ADDING_EXPENSE_CATEGORY
    except ValueError:
        await update.message.reply_text("❌ Не похоже на число."); return ADDING_EXPENSE_AMOUNT

async def add_expense_category(update, context):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard()); return CHOOSING_ACTION
    category = update.message.text if update.message.text in EXPENSE_CATEGORIES else "Другое"
    context.user_data["expense_category"] = category
    await update.message.reply_text("📝 Напиши, на что потратил:", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True))
    return ADDING_EXPENSE_DESC

async def add_expense_desc(update, context):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard()); return CHOOSING_ACTION
    amount = context.user_data.get("expense_amount", 0)
    category = context.user_data.get("expense_category", "Другое")
    success = add_transaction(-amount, category, update.message.text, CHILD_NAME)
    if success:
        balance = get_balance(CHILD_NAME)
        await update.message.reply_text(f"✅ -{amount:.0f} руб. записано! {category}\n💰 Баланс: *{balance:.2f} руб.*", parse_mode="Markdown", reply_markup=main_keyboard())
    else:
        await update.message.reply_text("❌ Ошибка.", reply_markup=main_keyboard())
    return CHOOSING_ACTION

async def show_goals(update, context):
    goals = get_goals(CHILD_NAME)
    kb = [[KeyboardButton("🎯 Добавить цель"), KeyboardButton("💰 Пополнить цель")],[KeyboardButton("🔙 Назад")]]
    if not goals:
        await update.message.reply_text("🎯 Целей пока нет. Поставь цель!", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    else:
        lines = ["🎯 *Цели:*\n"]
        for g in goals:
            bar = "🟩"*int(g["percent"]/10) + "⬜"*(10-int(g["percent"]/10))
            lines.append(f"*{g['name']}*\n{bar} {g['percent']}%\nНакоплено: {g['saved']:.0f}/{g['target']:.0f} руб.\n")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CHOOSING_ACTION

async def start_add_goal(update, context):
    await update.message.reply_text("🎯 Как называется цель? (велосипед, телефон...)", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True))
    return ADDING_GOAL_NAME

async def add_goal_name(update, context):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard()); return CHOOSING_ACTION
    context.user_data["goal_name"] = update.message.text
    await update.message.reply_text("💰 Сколько нужно накопить? Введи сумму:", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True))
    return ADDING_GOAL_AMOUNT

async def add_goal_amount(update, context):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard()); return CHOOSING_ACTION
    try:
        target = float(update.message.text.replace(",","."))
        goal_name = context.user_data.get("goal_name","Цель")
        if add_goal(CHILD_NAME, goal_name, target):
            await update.message.reply_text(f"✅ Цель *{goal_name}* — {target:.0f} руб. создана! 🚀", parse_mode="Markdown", reply_markup=main_keyboard())
        else:
            await update.message.reply_text("❌ Ошибка.", reply_markup=main_keyboard())
    except ValueError:
        await update.message.reply_text("❌ Не число."); return ADDING_GOAL_AMOUNT
    return CHOOSING_ACTION

async def start_save_for_goal(update, context):
    goals = get_goals(CHILD_NAME)
    if not goals:
        await update.message.reply_text("🎯 Целей нет. Создай цель!", reply_markup=main_keyboard()); return CHOOSING_ACTION
    buttons = [[KeyboardButton(g["name"])] for g in goals] + [[KeyboardButton("Отмена")]]
    await update.message.reply_text("🎯 Выбери цель:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    context.user_data["goals_list"] = goals
    return SAVING_FOR_GOAL_SELECT

async def select_goal_to_save(update, context):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard()); return CHOOSING_ACTION
    goals = context.user_data.get("goals_list",[])
    goal = next((g for g in goals if g["name"]==update.message.text), None)
    if not goal:
        await update.message.reply_text("❌ Цель не найдена.", reply_markup=main_keyboard()); return CHOOSING_ACTION
    context.user_data["selected_goal"] = goal
    await update.message.reply_text(f"💰 Сколько откладываешь на «{goal['name']}»?", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отмена")]], resize_keyboard=True))
    return SAVING_FOR_GOAL_AMOUNT

async def add_goal_savings(update, context):
    if update.message.text == "Отмена":
        await update.message.reply_text("Отменено.", reply_markup=main_keyboard()); return CHOOSING_ACTION
    try:
        amount = float(update.message.text.replace(",","."))
        goal = context.user_data.get("selected_goal",{})
        goal_name = goal.get("name","Цель")
        if update_goal_saved(CHILD_NAME, goal_name, amount):
            add_transaction(-amount,"Копилка",f"Пополнение: {goal_name}",CHILD_NAME)
            await update.message.reply_text(f"✅ Отложено {amount:.0f} руб. на «{goal_name}» 🎯", reply_markup=main_keyboard())
        else:
            await update.message.reply_text("❌ Ошибка.", reply_markup=main_keyboard())
    except ValueError:
        await update.message.reply_text("❌ Не число."); return SAVING_FOR_GOAL_AMOUNT
    return CHOOSING_ACTION

async def get_ai_advice(update, context):
    await update.message.reply_text("🤖 Анализирую финансы...", reply_markup=main_keyboard())
    advice = get_financial_advice(CHILD_NAME, get_balance(CHILD_NAME), get_transactions(CHILD_NAME), get_goals(CHILD_NAME))
    await update.message.reply_text(f"🤖 *Совет AI:*\n\n{advice}", parse_mode="Markdown", reply_markup=main_keyboard())
    return CHOOSING_ACTION

async def handle_back(update, context):
    await update.message.reply_text("Главное меню:", reply_markup=main_keyboard()); return CHOOSING_ACTION

async def unknown(update, context):
    await update.message.reply_text("Не понимаю 🤖 Используй кнопки меню.", reply_markup=main_keyboard()); return CHOOSING_ACTION

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
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
            ],
            ADDING_INCOME_AMOUNT:[MessageHandler(filters.TEXT&~filters.COMMAND,add_income_amount)],
            ADDING_INCOME_DESC:[MessageHandler(filters.TEXT&~filters.COMMAND,add_income_desc)],
            ADDING_EXPENSE_AMOUNT:[MessageHandler(filters.TEXT&~filters.COMMAND,add_expense_amount)],
            ADDING_EXPENSE_CATEGORY:[MessageHandler(filters.TEXT&~filters.COMMAND,add_expense_category)],
            ADDING_EXPENSE_DESC:[MessageHandler(filters.TEXT&~filters.COMMAND,add_expense_desc)],
            ADDING_GOAL_NAME:[MessageHandler(filters.TEXT&~filters.COMMAND,add_goal_name)],
            ADDING_GOAL_AMOUNT:[MessageHandler(filters.TEXT&~filters.COMMAND,add_goal_amount)],
            SAVING_FOR_GOAL_SELECT:[MessageHandler(filters.TEXT&~filters.COMMAND,select_goal_to_save)],
            SAVING_FOR_GOAL_AMOUNT:[MessageHandler(filters.TEXT&~filters.COMMAND,add_goal_savings)],
        },
        fallbacks=[CommandHandler("start",start),MessageHandler(filters.TEXT,unknown)],
        allow_reentry=True
    )
    app.add_handler(conv)
    logger.info(f"Бот запущен для {CHILD_NAME}...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
