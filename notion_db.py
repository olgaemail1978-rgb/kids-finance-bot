import requests
from datetime import datetime
from config import NOTION_TOKEN, NOTION_TRANSACTIONS_DB, NOTION_GOALS_DB

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


def add_transaction(amount: float, category: str, description: str, child_name: str):
    """Add a transaction to the Notion database."""
    url = f"https://api.notion.com/v1/pages"
    data = {
        "parent": {"database_id": NOTION_TRANSACTIONS_DB},
        "properties": {
            "Name": {
                "title": [{"text": {"content": description}}]
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
    resp = requests.post(url, headers=HEADERS, json=data)
    return resp.status_code == 200


def get_balance(child_name: str) -> float:
    """Calculate current balance for a child."""
    url = f"https://api.notion.com/v1/databases/{NOTION_TRANSACTIONS_DB}/query"
    data = {
        "filter": {
            "property": "Child",
            "rich_text": {"contains": child_name}
        }
    }
    resp = requests.post(url, headers=HEADERS, json=data)
    if resp.status_code != 200:
        return 0.0
    results = resp.json().get("results", [])
    balance = 0.0
    for item in results:
        props = item.get("properties", {})
        amount = props.get("Amount", {}).get("number", 0) or 0
        balance += amount
    return balance


def get_transactions(child_name: str, limit: int = 10) -> list:
    """Get recent transactions for a child."""
    url = f"https://api.notion.com/v1/databases/{NOTION_TRANSACTIONS_DB}/query"
    data = {
        "filter": {
            "property": "Child",
            "rich_text": {"contains": child_name}
        },
        "sorts": [{"property": "Date", "direction": "descending"}],
        "page_size": limit
    }
    resp = requests.post(url, headers=HEADERS, json=data)
    if resp.status_code != 200:
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


def add_goal(child_name: str, goal_name: str, target_amount: float) -> bool:
    """Add a savings goal."""
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
    resp = requests.post(url, headers=HEADERS, json=data)
    return resp.status_code == 200


def get_goals(child_name: str) -> list:
    """Get active savings goals for a child."""
    url = f"https://api.notion.com/v1/databases/{NOTION_GOALS_DB}/query"
    data = {
        "filter": {
            "and": [
                {"property": "Child", "rich_text": {"contains": child_name}},
                {"property": "Status", "select": {"equals": "Active"}}
            ]
        }
    }
    resp = requests.post(url, headers=HEADERS, json=data)
    if resp.status_code != 200:
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


def update_goal_saved(goal_id: str, amount: float) -> bool:
    """Add amount to a goal's saved balance."""
    # First get current saved amount
    url = f"https://api.notion.com/v1/pages/{goal_id}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return False
    props = resp.json().get("properties", {})
    current = props.get("Saved", {}).get("number", 0) or 0
    new_saved = current + amount

    # Update
    data = {
        "properties": {
            "Saved": {"number": new_saved}
        }
    }
    if new_saved >= (props.get("Target", {}).get("number", 0) or 0):
        data["properties"]["Status"] = {"select": {"name": "Completed"}}

    resp = requests.patch(url, headers=HEADERS, json=data)
    return resp.status_code == 200
