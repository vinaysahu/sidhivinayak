from num2words import num2words
import decimal

def format_indian_currency(amount):
    """
    Formats a number into Indian Currency format (e.g. ₹ 1,23,456.00)
    """
    if amount is None or amount == "":
        return "₹ 0.00"
    
    try:
        # Convert to decimal and round to 2 places
        amount_dec = decimal.Decimal(str(amount)).quantize(decimal.Decimal('0.01'))
    except (decimal.InvalidOperation, ValueError, TypeError):
        return "₹ 0.00"

    # Separate integer and decimal parts
    s = str(amount_dec)
    if "." in s:
        integer_part, decimal_part = s.split(".")
    else:
        integer_part, decimal_part = s, "00"

    # Handle negative amounts
    prefix = ""
    if integer_part.startswith("-"):
        prefix = "-"
        integer_part = integer_part[1:]

    # Last 3 digits of integer part
    last3 = integer_part[-3:]
    rest = integer_part[:-3]

    if rest != "":
        rest = rest[::-1]
        # Group in 2s
        parts = [rest[i:i+2] for i in range(0, len(rest), 2)]
        rest = ",".join(parts)[::-1]
        formatted_int = f"{rest},{last3}"
    else:
        formatted_int = last3

    return f"₹ {prefix}{formatted_int}.{decimal_part}"

def amount_to_words(amount):
    """
    Converts amount to words in Indian English format (e.g. One Lakh Twenty Three Thousand...)
    """
    try:
        if amount is None or amount == "" or decimal.Decimal(str(amount)) == 0:
            return "Zero Rupees Only"
    except (decimal.InvalidOperation, ValueError, TypeError):
        return "Zero Rupees Only"

    try:
        # num2words with lang='en_IN' handles Lakhs/Crores
        words = num2words(amount, lang='en_IN').title()
        # Clean up common issues if any
        words = words.replace("And", "and")
        return f"{words} Rupees Only"
    except Exception:
        return ""
