"""Vietnamese currency amount-in-words, matching how staff already write it
on paper forms (e.g. "Bốn mươi triệu bảy trăm nghìn đồng")."""

_DIGIT_WORDS = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
_GROUP_UNITS = ["", "nghìn", "triệu", "tỷ"]


def _read_three_digits(n: int, full: bool) -> str:
    """Reads a 0-999 chunk. `full` forces the hundreds word even when it's
    zero (used for any group that isn't the most-significant one, e.g. 705
    inside a larger number still needs "không trăm linh năm")."""
    hundreds, remainder = divmod(n, 100)
    tens, ones = divmod(remainder, 10)
    parts = []
    if hundreds or full:
        parts.append(f"{_DIGIT_WORDS[hundreds]} trăm")
    if tens == 0:
        if ones:
            if hundreds or full:
                parts.append("linh")
            parts.append(_DIGIT_WORDS[ones])
    elif tens == 1:
        parts.append("mười")
        if ones == 5:
            parts.append("lăm")
        elif ones:
            parts.append(_DIGIT_WORDS[ones])
    else:
        parts.append(f"{_DIGIT_WORDS[tens]} mươi")
        if ones == 1:
            parts.append("mốt")
        elif ones == 5:
            parts.append("lăm")
        elif ones:
            parts.append(_DIGIT_WORDS[ones])
    return " ".join(p for p in parts if p)


def amount_in_words_vi(amount: float | int) -> str:
    n = int(round(float(amount)))
    if n == 0:
        return "Không đồng"

    sign = "Âm " if n < 0 else ""
    n = abs(n)

    groups = []
    while n > 0:
        groups.append(n % 1000)
        n //= 1000

    words = []
    for i in range(len(groups) - 1, -1, -1):
        g = groups[i]
        if g == 0:
            continue
        text = _read_three_digits(g, full=(i < len(groups) - 1))
        unit = _GROUP_UNITS[i] if i < len(_GROUP_UNITS) else ""
        words.append(f"{text} {unit}".strip())

    result = " ".join(words)
    result = result[0].upper() + result[1:]
    return f"{sign}{result} đồng"
