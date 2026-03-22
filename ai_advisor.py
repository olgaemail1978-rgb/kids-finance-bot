# -*- coding: utf-8 -*-
import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def get_financial_advice(child_name: str, balance: float, transactions: list, goals: list) -> str:
    """Get AI financial advice for a child based on their financial data."""
    tx_text = ""
    if transactions:
        tx_lines = []
        for tx in transactions[:10]:
            sign = "+" if tx["amount"] > 0 else ""
            tx_lines.append(f"  {tx['date']}: {sign}{tx['amount']} руб. — {tx['category']} ({tx['description']})")
        tx_text = "Последние транзакции:\n" + "\n".join(tx_lines)
    else:
        tx_text = "Транзакций пока нет."

    goals_text = ""
    if goals:
        goal_lines = []
        for g in goals:
            goal_lines.append(f"  • {g['name']}: накоплено {g['saved']} из {g['target']} руб. ({g['percent']}%)")
        goals_text = "Цели накопления:\n" + "\n".join(goal_lines)
    else:
        goals_text = "Целей накопления пока нет."

    prompt = f"""Ты дружелюбный финансовый советник для детей. Твоя задача — помочь ребёнку по имени {child_name} научиться управлять деньгами.

Текущий баланс: {balance} руб.
{tx_text}
{goals_text}

Дай короткий, дружелюбный совет (3-4 предложения) на русском языке:
- Оцени текущую финансовую ситуацию
- Дай 1-2 конкретных совета по управлению деньгами
- Похвали за хорошие привычки, если они есть
- Используй простой язык, понятный ребёнку
- Будь позитивным и мотивирующим!"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def chat_with_advisor(child_name: str, question: str, balance: float = 0,
                      transactions: list = None, goals: list = None) -> str:
    """Answer any question from a child as a friendly personal financial advisor."""
    if transactions is None:
        transactions = []
    if goals is None:
        goals = []

    # Build financial context
    context_parts = [f"Баланс: {balance:.2f} руб."]

    if transactions:
        tx_lines = []
        for tx in transactions[:5]:
            sign = "+" if tx["amount"] > 0 else ""
            tx_lines.append(f"{sign}{tx['amount']} руб. — {tx['category']} ({tx['description']})")
        context_parts.append("Последние операции: " + "; ".join(tx_lines))

    if goals:
        goal_lines = [f"{g['name']} — {g['percent']}% ({g['saved']}/{g['target']} руб.)" for g in goals]
        context_parts.append("Цели накопления: " + ", ".join(goal_lines))

    context = "\n".join(context_parts)

    system_prompt = f"""Ты личный финансовый помощник и друг ребёнка по имени {child_name}.

Как ты общаешься:
- Коротко и по делу (2-5 предложений)
- Простым языком для детей 9-12 лет
- Примеры из жизни: игры, школа, карманные деньги, покупки
- Тёплый тон, как старший друг или классный учитель
- Немного юмора и эмодзи — уместно
- Всегда на русском языке
- Если вопрос не про деньги — ответь кратко и мягко переведи на финансовую тему

Текущие финансы ребёнка:
{context}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=system_prompt,
        messages=[{"role": "user", "content": question}]
    )
    return message.content[0].text


def explain_category(category: str, amount: float) -> str:
    """Explain what a spending category means for a child."""
    prompt = f"""Объясни ребёнку простыми словами, что означает трата {abs(amount)} рублей на "{category}".
Дай 1-2 предложения с советом — это хорошая или плохая трата? Как можно было бы сэкономить?
Отвечай по-русски, дружелюбно."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
