import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def get_financial_advice(child_name: str, balance: float, transactions: list, goals: list) -> str:
    """Get AI financial advice for a child based on their financial data."""

    # Format transactions for context
    tx_text = ""
    if transactions:
        tx_lines = []
        for tx in transactions[:10]:
            sign = "+" if tx["amount"] > 0 else ""
            tx_lines.append(f"  {tx['date']}: {sign}{tx['amount']} руб. — {tx['category']} ({tx['description']})")
        tx_text = "Последние транзакции:\n" + "\n".join(tx_lines)
    else:
        tx_text = "Транзакций пока нет."

    # Format goals
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
