"""Independent Python implementation of 3a, 3b and 3c.

It follows the assignment's definitions directly (plain loops, no SQL), so if the
SQL and the oracle agree, both are very likely right.
"""

from collections import defaultdict
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from data import Event, Subscription

WINDOW_DAYS = 30


def window(yesterday: date) -> list[date]:
    return [yesterday - timedelta(days=n) for n in range(WINDOW_DAYS - 1, -1, -1)]


def is_valid(s: Subscription) -> bool:
    return s.start_date is not None and (s.end_date is None or s.end_date > s.start_date)


def is_active_on(s: Subscription, day: date) -> bool:
    return is_valid(s) and s.start_date <= day and (s.end_date is None or day < s.end_date)


def active_users_by_day(events: list[Event], days: list[date]) -> dict[date, set[str]]:
    in_window = set(days)
    active: dict[date, set[str]] = defaultdict(set)
    for e in events:
        if e.user_id is not None and e.event_ts.date() in in_window:
            active[e.event_ts.date()].add(e.user_id)
    return active


def paying_products(subs_by_user: dict[str, list[Subscription]], user: str, day: date) -> set[str]:
    return {s.product for s in subs_by_user.get(user, []) if is_active_on(s, day)}


def expected_3a(subscriptions: list[Subscription], events: list[Event], yesterday: date) -> list[tuple]:
    days = window(yesterday)
    active = active_users_by_day(events, days)
    subs_by_user = _group_by_user(subscriptions)
    rows = []
    for day in days:
        products = {u: paying_products(subs_by_user, u, day) for u in active[day]}
        overall = sum(1 for p in products.values() if p)
        pro = sum(1 for p in products.values() if "pro" in p)
        mp = sum(1 for p in products.values() if "mp" in p)
        rows.append((day, overall, pro, mp))
    return rows


def expected_3b(subscriptions: list[Subscription], events: list[Event], yesterday: date) -> list[tuple]:
    days = window(yesterday)
    active = active_users_by_day(events, days)
    subs_by_user = _group_by_user(subscriptions)
    rows = []
    for day in days:
        n_active = len(active[day])
        n_paying = sum(1 for u in active[day] if paying_products(subs_by_user, u, day))
        rows.append((day, n_active, n_paying, percentage(n_paying, n_active)))
    return rows


def expected_3c(subscriptions: list[Subscription]) -> list[tuple]:
    subs_by_user = _group_by_user([s for s in subscriptions if is_valid(s)])
    rows = []
    for user, subs in subs_by_user.items():
        subs = sorted(subs, key=lambda s: s.subscription_id)
        for i, a in enumerate(subs):
            for b in subs[i + 1:]:
                if _overlap(a, b):
                    rows.append((
                        user,
                        a.subscription_id, a.product, a.start_date, a.end_date,
                        b.subscription_id, b.product, b.start_date, b.end_date,
                        a.product == b.product,
                        max(a.start_date, b.start_date),
                        _earliest_end(a.end_date, b.end_date),
                    ))
    return rows


def percentage(part: int, whole: int) -> Optional[Decimal]:
    if whole == 0:
        return None
    return (Decimal(100 * part) / Decimal(whole)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _overlap(a: Subscription, b: Subscription) -> bool:
    a_starts_before_b_ends = b.end_date is None or a.start_date < b.end_date
    b_starts_before_a_ends = a.end_date is None or b.start_date < a.end_date
    return a_starts_before_b_ends and b_starts_before_a_ends


def _earliest_end(x: Optional[date], y: Optional[date]) -> Optional[date]:
    ends = [e for e in (x, y) if e is not None]
    return min(ends) if ends else None


def _group_by_user(subscriptions: list[Subscription]) -> dict[str, list[Subscription]]:
    grouped: dict[str, list[Subscription]] = defaultdict(list)
    for s in subscriptions:
        grouped[s.user_id].append(s)
    return grouped
