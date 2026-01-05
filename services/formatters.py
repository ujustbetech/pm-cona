def format_number(value, kind="number"):
    if value is None:
        return "-"

    try:
        value = float(value)
    except Exception:
        return value

    if kind == "count":
        return f"{int(value):,}"

    if kind == "percent":
        return f"{value:.1f}%"

    if kind == "currency":
        if value >= 1e7:   # Crores
            return f"₹{value/1e7:.2f} Cr"
        elif value >= 1e5: # Lakhs
            return f"₹{value/1e5:.2f} L"
        elif value >= 1e3:
            return f"₹{value/1e3:.1f} K"
        else:
            return f"₹{value:,.0f}"

    return f"{value:,.2f}"
