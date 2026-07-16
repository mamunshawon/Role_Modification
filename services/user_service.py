import re


EMPTY_VALUES = {"", "nan", "none", "null"}


def parse_role_ids(value):
    if value is None:
        return []

    text = str(value).strip()
    if text.lower() in EMPTY_VALUES:
        return []

    role_ids = []
    for token in re.split(r"[,;|\s]+", text):
        token = token.strip()
        if not token or token.lower() in EMPTY_VALUES:
            continue

        try:
            numeric_value = float(token)
        except ValueError as exc:
            raise ValueError(f"Invalid role ID: {token}") from exc

        if not numeric_value.is_integer():
            raise ValueError(f"Invalid role ID: {token}")

        role_id = int(numeric_value)
        if role_id not in role_ids:
            role_ids.append(role_id)

    return role_ids


def fetch_user(session, config, user_id):
    params = {"page": 1, "pageSize": 10, "userId": user_id}

    response = session.request(
        "GET",
        config["environment"]["get_user_url"],
        params=params,
        timeout=config["processing"]["request_timeout"],
        verify=False
    )

    if response.status_code != 200:
        raise Exception(f"GET failed for userId={user_id}, status={response.status_code}, body={response.text}")

    data = response.json()

    if data.get("totalElements", 0) == 0:
        return None

    return data["content"][0]


def build_payload(user, role_addition_value=None, role_deletion_value=None):
    role_additions = parse_role_ids(role_addition_value)
    role_deletions = parse_role_ids(role_deletion_value)

    # Get existing roles exactly as returned
    existing_role_ids = [r["id"] for r in user.get("roleList", [])]

    # Normalize to integers where possible to safely compare role IDs
    normalized_ids = []
    for role_id in existing_role_ids:
        try:
            normalized_ids.append(int(role_id))
        except (TypeError, ValueError):
            # Keep as-is if it cannot be converted
            normalized_ids.append(role_id)

    # Start from existing roles, remove deleted roles, and avoid duplicates
    new_role_ids = []
    deletion_set = set(role_deletions)
    for role_id in normalized_ids:
        if role_id in deletion_set:
            continue
        if role_id not in new_role_ids:
            new_role_ids.append(role_id)

    # Add requested roles after deletion. If the same role exists in both Excel
    # columns, Role Addition wins and the role remains in the final payload.
    for role_id in role_additions:
        if role_id not in new_role_ids:
            new_role_ids.append(role_id)

    # Build roleList preserving the computed order
    new_role_list = [{"id": role_id} for role_id in new_role_ids]

    return {
        "userId": user["userId"],
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "designation": user.get("designation"),
        "contactNumber": user.get("contactNumber"),
        "organization": user.get("organization"),
        "orgDep": user.get("orgDep"),
        "ref1Data": user.get("ref1Data"),
        "ref2Data": user.get("ref2Data"),
        "status": user.get("status"),

        # Must match manual payload structure
        "clientList": [
            {"clientId": c["clientId"]}
            for c in user.get("clientList", [])
        ],

        "roleList": new_role_list
    }


def update_user(session, config, payload):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = session.request(
        "PUT",
        config["environment"]["update_user_url"],
        json=payload,
        headers=headers,
        timeout=config["processing"]["request_timeout"],
        verify=False
    )

    return response
