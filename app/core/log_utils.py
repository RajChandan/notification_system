def mask_email(email: str) -> str:
    if "@" not in email:
        return "***"

    local, domain = email.split("@", 1)

    visible = local[:2]

    return f"{visible}***@{domain}"


def mask_phone(phone: str) -> str:
    if len(phone) < 4:
        return "***"

    return f"***{phone[-4:]}"
