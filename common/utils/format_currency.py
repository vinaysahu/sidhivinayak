def format_indian_currency(amount):
    amount = int(amount)
    s = str(amount)
    
    # Last 3 digits
    last3 = s[-3:]
    rest = s[:-3]
    
    if rest != "":
        rest = rest[::-1]
        parts = [rest[i:i+2] for i in range(0, len(rest), 2)]
        rest = ",".join(parts)[::-1]
        return f"₹ {rest},{last3}"
    else:
        return f"₹ {last3}"