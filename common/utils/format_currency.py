def format_indian_currency(amount):
    from decimal import Decimal, InvalidOperation
    if amount is None or amount == "":
        return "₹ 0"
    try:
        amount_dec = Decimal(str(amount)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError, TypeError):
        return "₹ 0"

    s = str(amount_dec)
    if "." in s:
        integer_part, decimal_part = s.split(".")
    else:
        integer_part, decimal_part = s, "00"

    prefix = ""
    if integer_part.startswith("-"):
        prefix = "-"
        integer_part = integer_part[1:]

    last3 = integer_part[-3:]
    rest = integer_part[:-3]

    if rest:
        rest = rest[::-1]
        parts = [rest[i:i+2] for i in range(0, len(rest), 2)]
        rest = ",".join(parts)[::-1]
        formatted_int = f"{rest},{last3}"
    else:
        formatted_int = last3

    if decimal_part == "00":
        return f"₹ {prefix}{formatted_int}"
    return f"₹ {prefix}{formatted_int}.{decimal_part}"