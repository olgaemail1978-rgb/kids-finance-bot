# -*- coding: utf-8 -*-
import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ──────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────

def _compute_stats(transactions: list):
    """Считает доход, расходы и топ-категорию из списка транзакций."""
    income = sum(tx.get("amount", 0) for tx in transactions if tx.get("amount", 0) > 0)
    expenses = sum(abs(tx.get("amount", 0)) for tx in transactions if tx.get("amount", 0) < 0)

    expense_by_cat = {}
    for tx in transactions:
        if tx.get("amount", 0) < 0:
            cat = tx.get("category", "Другое")
            expense_by_cat[cat] = expense_by_cat.get(cat, 0) + abs(tx["amount"])

    top_category = max(expense_by_cat, key=expense_by_cat.get) if expense_by_cat else "нет данных"
    return income, expenses, top_category


def _format_transactions(transactions: list, limit: int = 5) -> str:
    """Форматирует последние N транзакций в одну строку."""
    if not transactions:
        return "операций пока нет"
    lines = []
    for tx in transactions[:limit]:
        sign = "+" if tx.get("amount", 0) > 0 else "−"
        amt = abs(tx.get("amount", 0))
        cat = tx.get("category", "")
        desc = tx.get("description", "")
        lines.append(f"{sign}{amt:.0f}€ {cat} ({desc})")
    return " / ".join(lines)


def _format_goals(goals: list) -> str:
    """Форматирует цели накопления в строку."""
    if not goals:
        return "целей пока нет"
    return ", ".join(f"{g['name']} ({g['percent']}%)" for g in goals)


# ──────────────────────────────────────────────
# Основные функции
# ──────────────────────────────────────────────

def get_financial_advice(child_name: str, balance: float, transactions: list,
                         goals: list, child_age: int = 10) -> str:
    """Совет по кнопке «Совет AI» — персонаж Монеткин."""
    income, expenses, top_category = _compute_stats(transactions)
    recent = _format_transactions(transactions, 5)
    goals_text = _format_goals(goals)

    prompt = f"""Ты — Монеткин 🪙, весёлый и мудрый друг-копилка {child_name}.
Тебе {child_age} лет, ты говоришь как старший друг — просто, тепло, с юмором.

Финансы {child_name} за этот месяц:
💰 Баланс: {balance:.2f} €
⬆️ Доходы: {income:.2f} €
⬇️ Расходы: {expenses:.2f} €
📂 Больше всего потрачено на: {top_category}
🎯 Цели: {goals_text}
📋 Последние 5 операций: {recent}

Твой ответ должен:
1. Начаться с обращения по имени и эмодзи
2. Сказать что-то конкретное про его траты — не общее, а про реальные цифры
3. Дать ОДИН конкретный совет что можно улучшить
4. Похвалить за что-то хорошее если есть
5. Закончить мотивирующей фразой про цель

Стиль: как будто пишешь другу в Telegram. Коротко — 4-5 предложений максимум.
Никаких списков и заголовков — только живой текст с эмодзи.
Всегда на русском языке."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def chat_with_advisor(child_name: str, question: str, balance: float = 0,
                      transactions: list = None, goals: list = None,
                      child_age: int = 10) -> str:
    """Ответ на любой свободный текст — персонаж Монеткин."""
    if transactions is None:
        transactions = []
    if goals is None:
        goals = []

    income, expenses, top_category = _compute_stats(transactions)
    recent = _format_transactions(transactions, 5)
    goals_text = _format_goals(goals)

    system_prompt = f"""Ты — Монеткин 🪙, личный финансовый друг {child_name} ({child_age} лет).

Ты знаешь всё о финансах {child_name}:
💰 Баланс сейчас: {balance:.2f} €
📊 За этот месяц потрачено: {expenses:.2f} €
🏆 Топ расходов: {top_category}
🎯 Мечтает накопить на: {goals_text}
📋 Последние операции: {recent}

Правила общения:
— Отвечай как живой друг в Telegram, не как робот
— Используй конкретные цифры из финансов ребёнка
— Если спрашивает про деньги — дай реальный совет с примером
— Если спрашивает не про деньги — ответь коротко и мягко переведи на финансовую тему
— Иногда задавай встречный вопрос чтобы разговор был живым
— Возраст 9-12 лет: простые слова, примеры из жизни (игры, школа, друзья)
— Никогда не пиши длинные списки — только живой разговорный текст
— 3-5 предложений максимум
— Всегда на русском языке
— Эмодзи использовать уместно, не перебарщивать"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=system_prompt,
        messages=[{"role": "user", "content": question}]
    )
    return message.content[0].text


def explain_category(category: str, amount: float) -> str:
    """Объяснить ребёнку что значит трата в конкретной категории."""
    prompt = f"""Объясни ребёнку простыми словами, что означает трата {abs(amount):.0f}€ на "{category}".
Дай 1-2 предложения с советом — это хорошая или плохая трата? Как можно было бы сэкономить?
Отвечай по-русски, дружелюбно."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
