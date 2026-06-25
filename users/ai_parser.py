"""
Offline natural-language expense parser + auto-categorizer.

No external API, no keys, no network. Pure Python + regex.
Handles inputs like:
    "spent 450 on biryani yesterday"
    "300 petrol"
    "netflix 199 on 5 june"
    "bought a dress for 1200 last monday"
"""

import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation


CATEGORIES = ['Food', 'Travel', 'Shopping', 'Bills', 'Education', 'Other']

# Keyword -> category map, tuned from real spending vocabulary.
# Keys are matched as whole-ish words (substring, lowercased).
CATEGORY_KEYWORDS = {
    'Food': [
        'biriyani', 'biryani', 'pizza', 'burger', 'fries', 'kfc', 'mcd',
        'mcdonald', 'momos', 'meal', 'meals', 'snack', 'snacks', 'lunch',
        'dinner', 'breakfast', 'food', 'cafe', 'coffee', 'tea', 'chai',
        'restaurant', 'zomato', 'swiggy', 'rice', 'chicken', 'shawarma',
        'juice', 'icecream', 'ice cream', 'cake', 'bakery', 'laban', 'lime',
        'roll', 'dosa', 'idli', 'paratha', 'samosa', 'chips', 'drink',
    ],
    'Travel': [
        'petrol', 'diesel', 'fuel', 'uber', 'ola', 'rapido', 'auto',
        'taxi', 'cab', 'metro', 'bus', 'train', 'flight', 'ticket',
        'travel', 'parking', 'toll', 'ride', 'fare',
    ],
    'Shopping': [
        'dress', 'dresss', 'shirt', 'tshirt', 't-shirt', 'jeans', 'shoes',
        'necklace', 'glasses', 'jhumka', 'jhumkas', 'earring', 'lip tint',
        'lipstick', 'makeup', 'clothes', 'bag', 'watch', 'shopping',
        'amazon', 'flipkart', 'myntra', 'accessory', 'accessories',
        'cosmetic', 'perfume', 'jewellery', 'jewelry',
    ],
    'Bills': [
        'netflix', 'spotify', 'claude', 'chatgpt', 'youtube', 'prime',
        'hotstar', 'recharge', 'subscription', 'electricity', 'water bill',
        'wifi', 'internet', 'broadband', 'rent', 'bill', 'emi', 'insurance',
        'phone bill', 'mobile recharge', 'gas bill', 'dth',
    ],
    'Education': [
        'book', 'books', 'course', 'tuition', 'class', 'fees', 'fee',
        'exam', 'notebook', 'pen', 'stationery', 'udemy', 'coursera',
        'workshop', 'seminar', 'college', 'school',
    ],
}


# ---------------------------------------------------------------------------
# DATE PARSING
# ---------------------------------------------------------------------------

WEEKDAYS = {
    'monday': 0, 'mon': 0,
    'tuesday': 1, 'tue': 1, 'tues': 1,
    'wednesday': 2, 'wed': 2,
    'thursday': 3, 'thu': 3, 'thurs': 4,
    'friday': 4, 'fri': 4,
    'saturday': 5, 'sat': 5,
    'sunday': 6, 'sun': 6,
}

MONTHS = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
    'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
    'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10, 'nov': 11, 'november': 11,
    'dec': 12, 'december': 12,
}


def _parse_date(text, today=None):
    """Return (date_obj, matched_string_or_None)."""
    if today is None:
        today = date.today()
    t = text.lower()

    # today / tonight
    m = re.search(r'\b(today|tonight)\b', t)
    if m:
        return today, m.group(0)

    # yesterday
    m = re.search(r'\byesterday\b', t)
    if m:
        return today - timedelta(days=1), m.group(0)

    # "day before yesterday"
    m = re.search(r'\bday before yesterday\b', t)
    if m:
        return today - timedelta(days=2), m.group(0)

    # tomorrow (allow, though unusual for expenses)
    m = re.search(r'\btomorrow\b', t)
    if m:
        return today + timedelta(days=1), m.group(0)

    # "last <weekday>" or just "<weekday>"
    m = re.search(r'\b(?:last\s+)?(' + '|'.join(WEEKDAYS.keys()) + r')\b', t)
    if m:
        target = WEEKDAYS[m.group(1)]
        delta = (today.weekday() - target) % 7
        delta = delta or 7  # most recent past occurrence (not today)
        return today - timedelta(days=delta), m.group(0)

    # "5 june", "5th june", "june 5", "june 5th"
    day_month = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(' + '|'.join(MONTHS.keys()) + r')\b', t)
    month_day = re.search(r'\b(' + '|'.join(MONTHS.keys()) + r')\s+(\d{1,2})(?:st|nd|rd|th)?\b', t)
    if day_month:
        d = int(day_month.group(1))
        mo = MONTHS[day_month.group(2)]
        year = today.year if mo <= today.month else today.year
        try:
            return date(year, mo, d), day_month.group(0)
        except ValueError:
            pass
    if month_day:
        mo = MONTHS[month_day.group(1)]
        d = int(month_day.group(2))
        try:
            return date(today.year, mo, d), month_day.group(0)
        except ValueError:
            pass

    # numeric dd/mm or dd-mm (optionally /yyyy)
    m = re.search(r'\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b', t)
    if m:
        d = int(m.group(1))
        mo = int(m.group(2))
        y = m.group(3)
        if y:
            y = int(y)
            if y < 100:
                y += 2000
        else:
            y = today.year
        try:
            return date(y, mo, d), m.group(0)
        except ValueError:
            pass

    # "N days ago"
    m = re.search(r'\b(\d{1,2})\s+days?\s+ago\b', t)
    if m:
        return today - timedelta(days=int(m.group(1))), m.group(0)

    return today, None  # default to today, nothing matched


# ---------------------------------------------------------------------------
# AMOUNT PARSING
# ---------------------------------------------------------------------------

def _parse_amount(text):
    """Return (Decimal_or_None, matched_string_or_None)."""
    t = text.lower()

    # Prefer a number attached to a currency cue: ₹450, rs 450, 450 rupees, inr 450
    cue = re.search(
        r'(?:₹|rs\.?|inr|rupees?)\s*([\d,]+(?:\.\d{1,2})?)'
        r'|([\d,]+(?:\.\d{1,2})?)\s*(?:₹|rs\.?|inr|rupees?|bucks?)',
        t
    )
    if cue:
        raw = cue.group(1) or cue.group(2)
        val = _to_decimal(raw)
        if val is not None:
            return val, cue.group(0)

    # Otherwise: the largest standalone number in the text is most likely the price.
    candidates = re.findall(r'\b\d[\d,]*(?:\.\d{1,2})?\b', t)
    # filter out things that look like dates (1-2 digit day next to a month handled earlier)
    best = None
    best_raw = None
    for c in candidates:
        val = _to_decimal(c)
        if val is None:
            continue
        if best is None or val > best:
            best = val
            best_raw = c
    return best, best_raw


def _to_decimal(raw):
    try:
        return Decimal(raw.replace(',', ''))
    except (InvalidOperation, AttributeError):
        return None


# ---------------------------------------------------------------------------
# CATEGORY
# ---------------------------------------------------------------------------

def categorize(item_text):
    """Guess a category from item text. Returns one of CATEGORIES."""
    t = (item_text or '').lower()
    scores = {c: 0 for c in CATEGORIES}
    for cat, words in CATEGORY_KEYWORDS.items():
        for w in words:
            if w in t:
                # longer keyword = stronger signal
                scores[cat] += len(w.split()) + 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'Other'


# ---------------------------------------------------------------------------
# ITEM NAME EXTRACTION
# ---------------------------------------------------------------------------

FILLER = {
    'spent', 'spend', 'paid', 'pay', 'bought', 'buy', 'got', 'on', 'for',
    'a', 'an', 'the', 'of', 'to', 'at', 'in', 'today', 'tonight',
    'yesterday', 'tomorrow', 'last', 'rs', 'inr', 'rupees', 'rupee', 'bucks',
    'day', 'before', 'ago', 'days',
}


def _extract_item(text, amount_str, date_str):
    """Remove amount + date fragments + filler, leaving the item name."""
    t = ' ' + text + ' '

    # remove the matched amount and date substrings
    for frag in (amount_str, date_str):
        if frag:
            t = re.sub(re.escape(frag), ' ', t, flags=re.IGNORECASE)

    # remove currency symbols and stray numbers
    t = re.sub(r'[₹]', ' ', t)
    t = re.sub(r'\b\d[\d,]*(?:\.\d{1,2})?\b', ' ', t)

    # remove weekday words that may remain
    for wd in WEEKDAYS:
        t = re.sub(r'\b' + wd + r'\b', ' ', t, flags=re.IGNORECASE)
    for mo in MONTHS:
        t = re.sub(r'\b' + mo + r'\b', ' ', t, flags=re.IGNORECASE)

    # drop filler words
    words = [w for w in re.split(r'\s+', t) if w and w.lower() not in FILLER]
    item = ' '.join(words).strip(' -+.,')

    return item if item else 'Expense'


# ---------------------------------------------------------------------------
# PUBLIC ENTRY POINT
# ---------------------------------------------------------------------------

def parse_expense(text, today=None):
    """
    Parse a natural-language expense string.

    Returns a dict:
        {
          'item_name': str,
          'category': str,
          'amount': str | None,   # decimal as string, or None if not found
          'expense_date': 'YYYY-MM-DD',
          'confident': bool       # False if amount missing
        }
    """
    if today is None:
        today = date.today()

    text = (text or '').strip()
    if not text:
        return {
            'item_name': '', 'category': 'Other', 'amount': None,
            'expense_date': today.isoformat(), 'confident': False,
        }

    dt, date_str = _parse_date(text, today=today)
    amount, amount_str = _parse_amount(text)
    item = _extract_item(text, amount_str, date_str)
    category = categorize(item if item != 'Expense' else text)

    return {
        'item_name': item,
        'category': category,
        'amount': str(amount) if amount is not None else None,
        'expense_date': dt.isoformat(),
        'confident': amount is not None,
    }


# ---------------------------------------------------------------------------
# SPENDING INSIGHTS (offline, data-driven)
# ---------------------------------------------------------------------------

def generate_insights(this_month, last_month, budget_limit=None, days_elapsed=None, days_in_month=None):
    """
    Build a few accurate, plain-English insight strings from real numbers.

    this_month / last_month: dict {category: total_float}
    budget_limit: float or None (overall monthly cap)
    Returns a list of {'icon': fa-name, 'text': str, 'tone': 'ok'|'warn'|'info'}.
    """
    insights = []

    total_now = sum(this_month.values())
    total_prev = sum(last_month.values())

    if total_now == 0:
        return [{
            'icon': 'fa-circle-info',
            'text': "No spending recorded yet this month. Add an expense to see insights.",
            'tone': 'info',
        }]

    # 1) Month-over-month total trend
    if total_prev > 0:
        change = ((total_now - total_prev) / total_prev) * 100
        if abs(change) >= 5:
            direction = "more" if change > 0 else "less"
            tone = 'warn' if change > 0 else 'ok'
            icon = 'fa-arrow-trend-up' if change > 0 else 'fa-arrow-trend-down'
            insights.append({
                'icon': icon,
                'text': f"You've spent {abs(change):.0f}% {direction} than last month so far (₹{total_now:.0f} vs ₹{total_prev:.0f}).",
                'tone': tone,
            })

    # 2) Biggest category and its share
    if this_month:
        top_cat = max(this_month, key=this_month.get)
        top_amt = this_month[top_cat]
        share = (top_amt / total_now) * 100
        insights.append({
            'icon': 'fa-chart-pie',
            'text': f"{top_cat} is your biggest category at ₹{top_amt:.0f} — {share:.0f}% of this month's spending.",
            'tone': 'info',
        })

    # 3) Category that jumped the most vs last month
    jumps = []
    for cat, amt in this_month.items():
        prev = last_month.get(cat, 0)
        if prev > 0 and amt > prev:
            pct = ((amt - prev) / prev) * 100
            if pct >= 25:
                jumps.append((cat, pct, amt))
    if jumps:
        jumps.sort(key=lambda x: x[1], reverse=True)
        cat, pct, amt = jumps[0]
        insights.append({
            'icon': 'fa-circle-exclamation',
            'text': f"{cat} spending is up {pct:.0f}% from last month.",
            'tone': 'warn',
        })

    # 4) Budget pace projection
    if budget_limit and budget_limit > 0 and days_elapsed and days_in_month and days_elapsed > 0:
        daily_rate = total_now / days_elapsed
        projected = daily_rate * days_in_month
        if projected > budget_limit:
            over = projected - budget_limit
            insights.append({
                'icon': 'fa-triangle-exclamation',
                'text': f"At this pace you'll reach about ₹{projected:.0f} by month-end — ₹{over:.0f} over your ₹{budget_limit:.0f} budget.",
                'tone': 'warn',
            })
        else:
            insights.append({
                'icon': 'fa-circle-check',
                'text': f"On track — projected ₹{projected:.0f} by month-end, within your ₹{budget_limit:.0f} budget.",
                'tone': 'ok',
            })

    return insights[:4]