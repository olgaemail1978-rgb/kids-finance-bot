# -*- coding: utf-8 -*-
import requests
import logging
from datetime import datetime
from config import NOTION_TOKEN, NOTION_TRANSACTIONS_DB, NOTION_GOALS_DB

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


def add_transaction(amount: float, category: str, description: str, child_name: str) -> tuple:
    """Add a transaction to the Notion database. Returns (success, error_msg)."""
    if not NOTION_TRANSACTIONS_DB:
        return False, "NOTION_TRANSACTIONS_DB не настроен в переменных окружения"

    url = "https://api.notion.com/v1/pages"
    data = {
        "parent": {"database_id": NOTION_TRANSACTIONS_DB},
        "properties": {
            "Name": {
                "title": [{"text": {"content": description or "Без описания"}}]
            },
            "Amount": {
                "number": amount
            },
            "Category": {
                "select": {"name": category}
            },
            "Child": {
                "rich_text": [{"text": {"content": child_name}}]
            },
            "Date": {
                "date": {"start": datetime.now().isoformat()}
            },
            "Type": {
                "select": {"name": "Income" if amount > 0 else "Expense"}
            }
        }
    }

    try:
        resp = requests.post(url, headers=HEADERS, json=data, timeout=15)
        if resp.status_code == 200:
            return True, ""
        else:
            error_msg = f"HTTP {resp.status_code}"
            try:
                body = resp.json()
                error_msg += f": {body.get('message', body.get('code', resp.text[:200]))}"
            except Exception:
                error_msg += f": {resp.text[:200]}"
            logger.error(f"Notion add_transaction failed: {error_msg}")
            return False, error_msg
    except requests.exceptions.Timeout:
        logger.error("Notion add_transaction: timeout")
        return False, "Таймаут соединения с Notion"
    except Exception as e:
        logger.error(f"Notion add_transaction exception: {e}")
        return False, str(e)


def get_balance(child_name: str) -> float:
    """Calculate current balance for a child."""
    if not NOTION_TRANSACTIONS_DB:
        return 0.0

    url = f"https://api.notion.com/v1/databases/{NOTION_TRANSACTIONS_DB}/query"
    data = {
        "filter": {
            "property": "Child",
            "rich_text": {"contains": child_name}
        }
    }
    try:
        resp = requests.post(url, headers=HEADERS, json=data, timeout=15)
        if resp.status_code != 200:
            logger.error(f"get_balance error: {resp.status_code} {resp.text[:200]}")
            return 0.0
        results = resp.json().get("results", [])
        balance = 0.0
        for item in results:
            props = item.get("properties", {})
            amount = props.get("Amount", {}).get("number", 0) or 0
            balance += amount
        return balance
    except Exception as e:
        logger.error(f"get_balance exception: {e}")
        return 0.0


def get_transactions(child_name: str, limit: int = 10) -> list:
    """Get recent transactions for a child."""
    if not NOTION_TRANSACTIONS_DB:
        return []

    url = f"https://api.notion.com/v1/databases/{NOTION_TRANSACTIONS_DB}/query"
    data = {
        "filter": {
            "property": "Child",
            "rich_text": {"contains": child_name}
        },
        "sorts": [{"property": "Date", "direction": "descending"}],
        "page_size": limit
    }
    try:
        resp = requests.post(url, headers=HEADERS, json=data, timeout=15)
        if resp.status_code != 200:
            logger.error(f"get_transactions error: {resp.status_code} {resp.text[:200]}")
            return []
        results = resp.json().get("results", [])
        transactions = []
        for item in results:
            props = item.get("properties", {})
            amount = props.get("Amount", {}).get("number", 0) or 0
            category = props.get("Category", {}).get("select", {})
            category_name = category.get("name", "Другое") if category else "Другое"
            title_arr = props.get("Name", {}).get("title", [])
            description = title_arr[0]["text"]["content"] if title_arr else ""
            date_obj = props.get("Date", {}).get("date", {})
            date_str = date_obj.get("start", "")[:10] if date_obj else ""
            transactions.append({
                "amount": amount,
                "category": category_name,
                "description": description,
                "date": date_str
            })
        return transactions
    except Exception as e:
        logger.error(f"get_transactions exception: {e}")
        return []


def add_goal(child_name: str, goal_name: str, target_amount: float) -> tuple:
    """Add a savings goal. Returns (success, error_msg)."""
    if not NOTION_GOALS_DB:
        return False, "NOTION_GOALS_DB не настроен в переменных окружения"

    url = "https://api.notion.com/v1/pages"
    data = {
        "parent": {"database_id": NOTION_GOALS_DB},
        "properties": {
            "Name": {
                "title": [{"text": {"content": goal_name}}]
            },
            "Target": {
                "number": target_amount
            },
            "Saved": {
                "number": 0
            },
            "Child": {
                "rich_text": [{"text": {"content": child_name}}]
            },
            "Status": {
                "select": {"name": "Active"}
            }
        }
    }
    try:
        resp = requests.post(url, headers=HEADERS, json=data, timeout=15)
        if resp.status_code == 200:
            return True, ""
        else:
            error_msg = f"HTTP {resp.status_code}"
            try:
                body = resp.json()
                error_msg += f": {body.get('message', resp.text[:200])}"
            except Exception:
                error_msg += f": {resp.text[:200]}"
            logger.error(f"Notion add_goal failed: {error_msg}")
            return False, error_msg
    except Exception as e:
        logger.error(f"add_goal exception: {e}")
        return False, str(e)


def get_goals(child_name: str) -> list:
    """Get active savings goals for a child."""
    if not NOTION_GOALS_DB:
        return []

    url = f"https://api.notion.com/v1/databases/{NOTION_GOALS_DB}/query"
    data = {
        "filter": {
            "and": [
                {"property": "Child", "rich_text": {"contains": child_name}},
                {"property": "Status", "select": {"equals": "Active"}}
            ]
        }
    }
    try:
        resp = requests.post(url, headers=HEADERS, json=data, timeout=15)
        if resp.status_code != 200:
            logger.error(f"get_goals error: {resp.status_code} {resp.text[:200]}")
            return []
        results = resp.json().get("results", [])
        goals = []
        for item in results:
            props = item.get("properties", {})
            title_arr = props.get("Name", {}).get("title", [])
            name = title_arr[0]["text"]["content"] if title_arr else ""
            target = props.get("Target", {}).get("number", 0) or 0
            saved = props.get("Saved", {}).get("number", 0) or 0
            goals.append({
                "id": item["id"],
                "name": name,
                "target": target,
                "saved": saved,
                "percent": round((saved / target * 100) if target > 0 else 0, 1)
            })
        return goals
    except Exception as e:
        logger.error(f"get_goals exception: {e}")
        return []


def update_goal_saved(goal_id: str, amount: float) -> tuple:
    """Add amount to a goal's saved balance. Returns (success, error_msg)."""
    url = f"https://api.notion.com/v1/pages/{goal_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return False, f"Не удалось получить цель: HTTP {resp.status_code}"

        props = resp.json().get("properties", {})
        current = props.get("Saved", {}).get("number", 0) or 0
        new_saved = current + amount
        target = props.get("Target", {}).get("number", 0) or 0

        data = {"properties": {"Saved": {"number": new_saved}}}
        if new_saved >= target > 0:
            data["properties"]["Status"] = {"select": {"name": "Completed"}}

        resp = requests.patch(url, headers=HEADERS, json=data, timeout=15)
        if resp.status_code == 200:
            return True, ""
        else:
            return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
    except Exception as e:
        logger.error(f"update_goal_saved exception: {e}")
        return False, str(e)
