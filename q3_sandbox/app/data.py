"""Test data for the Q3 queries: hand-made edge cases and random bulk data.

All dates are relative to `yesterday` (the last day of the 30-day window), so the
data stays meaningful whatever day it is generated.
"""

import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional


@dataclass(frozen=True)
class Subscription:
    subscription_id: int
    user_id: str
    product: str
    start_date: Optional[date]
    end_date: Optional[date]


@dataclass(frozen=True)
class Event:
    event_ts: datetime
    user_id: Optional[str]
    event_name: str


@dataclass
class Dataset:
    users: list[str]
    subscriptions: list[Subscription]
    events: list[Event]


def _at(day: date, hh: int = 10, mm: int = 0, ss: int = 0) -> datetime:
    return datetime.combine(day, time(hh, mm, ss))


def edge_cases(yesterday: date) -> Dataset:
    """One user per edge case. Expected results are written by hand in `expected_edge_results`."""
    y = yesterday
    first_day = y - timedelta(days=29)

    def d(offset: int) -> date:
        return y + timedelta(days=offset)

    subscriptions = [
        Subscription(1, "u_pro_open", "pro", d(-40), None),
        Subscription(2, "u_ends_yesterday", "pro", d(-60), d(0)),        # end_date = first inactive day
        Subscription(3, "u_both_products", "pro", d(-40), None),
        Subscription(4, "u_both_products", "mp", d(-20), None),
        Subscription(5, "u_starts_yesterday", "mp", d(0), None),
        Subscription(6, "u_paying_no_events", "pro", d(-40), None),
        Subscription(7, "u_renewal", "pro", d(-200), d(-100)),           # next one starts the day this one ends
        Subscription(8, "u_renewal", "pro", d(-100), None),
        Subscription(9, "u_duplicate_pro", "pro", d(-40), None),
        Subscription(10, "u_duplicate_pro", "pro", d(-10), d(6)),
        Subscription(11, "u_zero_length", "pro", d(-20), d(-20)),        # active on no day
        Subscription(12, "u_zero_length", "mp", d(-25), None),
        Subscription(13, "u_inverted", "pro", d(-10), d(-40)),           # invalid: ends before it starts
        Subscription(14, "u_null_start", "pro", None, None),             # invalid: no start
        Subscription(15, "u_cross_product", "mp", d(-60), None),
        Subscription(16, "u_cross_product", "pro", d(-10), d(-5)),
        Subscription(17, "u_three_way", "pro", d(-50), None),
        Subscription(18, "u_three_way", "pro", d(-30), d(-1)),
        Subscription(19, "u_three_way", "mp", d(-20), d(10)),
        Subscription(20, "u_future", "pro", d(5), None),                 # starts after the window
        Subscription(21, "u_ended_before_window", "pro", d(-100), d(-50)),
    ]

    events = [
        Event(_at(d(0)), "u_pro_open", "view"),
        Event(_at(first_day - timedelta(days=1), 23, 59, 59), "u_pro_open", "view"),  # 1 second before the window
        Event(_at(d(1), 0, 0, 0), "u_pro_open", "view"),                               # today: after the window
        Event(_at(first_day, 0, 0, 0), "u_pro_open", "view"),                          # first second of the window
        Event(_at(d(-1), 9), "u_ends_yesterday", "view"),
        Event(_at(d(0), 9), "u_ends_yesterday", "view"),
        Event(_at(d(0), 12), "u_both_products", "view"),
        Event(_at(d(0), 13), None, "view"),                                            # anonymous
        Event(_at(d(-1), 13), None, "view"),                                           # anonymous
        Event(_at(d(0), 0, 0, 0), "u_starts_yesterday", "view"),
        Event(_at(d(-5)), "u_renewal", "view"),
        Event(_at(d(0), 8), "u_duplicate_pro", "view"),
        Event(_at(d(0), 23, 59, 59), "u_duplicate_pro", "view"),
        Event(_at(d(-20)), "u_zero_length", "view"),
        Event(_at(d(-15)), "u_inverted", "view"),
        Event(_at(d(-2)), "u_null_start", "view"),
        Event(_at(d(-7)), "u_cross_product", "view"),
        Event(_at(d(-2)), "u_three_way", "view"),
        Event(_at(d(0)), "u_future", "view"),
        Event(_at(d(-3)), "u_ended_before_window", "view"),
        Event(_at(d(0), 14), "u_orphan", "view"),                                      # not in users
        Event(_at(d(0), 15), "u_no_subscription", "view"),
    ]

    users = sorted({s.user_id for s in subscriptions} | {"u_no_subscription"})
    return Dataset(users, subscriptions, events)


def expected_edge_results(yesterday: date) -> dict:
    """Hand-computed results for `edge_cases`. Days not listed are empty (0 users, NULL percentage)."""
    y = yesterday

    def d(offset: int) -> date:
        return y + timedelta(days=offset)

    q3a = {  # day: (overall, pro, mp)
        d(0): (4, 3, 2),     # pro_open, both_products (once), starts_yesterday, duplicate_pro (once)
        d(-1): (1, 1, 0),    # ends_yesterday is still paying the day before its end_date
        d(-2): (1, 1, 1),    # three_way; null_start is active but not paying
        d(-5): (1, 1, 0),    # renewal
        d(-7): (1, 1, 1),    # cross_product
        d(-20): (1, 0, 1),   # zero_length counts through its mp subscription only
        d(-29): (1, 1, 0),   # pro_open at 00:00:00 on the first day of the window
    }
    q3b = {  # day: (active, paying)
        d(0): (8, 4),        # + ends_yesterday, future, orphan, no_subscription (active, not paying)
        d(-1): (1, 1),
        d(-2): (2, 1),
        d(-3): (1, 0),       # ended_before_window
        d(-5): (1, 1),
        d(-7): (1, 1),
        d(-15): (1, 0),      # inverted subscription doesn't count (and doesn't crash the query)
        d(-20): (1, 1),
        d(-29): (1, 1),
    }
    q3c = {  # (user, id_1, id_2): (same_product, overlap_start, overlap_end)
        ("u_both_products", 3, 4): (False, d(-20), None),
        ("u_duplicate_pro", 9, 10): (True, d(-10), d(6)),
        ("u_cross_product", 15, 16): (False, d(-10), d(-5)),
        ("u_three_way", 17, 18): (True, d(-30), d(-1)),
        ("u_three_way", 17, 19): (False, d(-20), d(10)),
        ("u_three_way", 18, 19): (False, d(-20), d(-1)),
    }
    return {"q3a": q3a, "q3b": q3b, "q3c": q3c}


def random_data(yesterday: date, n_users: int, seed: int, first_subscription_id: int) -> Dataset:
    """Random users mixed with a few bad rows, to compare the queries with the Python oracle at volume."""
    rng = random.Random(seed)
    users = [f"r{i:06d}" for i in range(n_users)]
    subscriptions: list[Subscription] = []
    events: list[Event] = []
    next_id = first_subscription_id

    for user in users:
        if rng.random() < 0.6:
            for _ in range(rng.randint(1, 3)):
                subscriptions.append(_random_subscription(rng, next_id, user, yesterday))
                next_id += 1
        for offset in range(-35, 2):                      # a few days either side of the window
            if rng.random() < 0.3:
                day = yesterday + timedelta(days=offset)
                for _ in range(rng.randint(1, 3)):
                    events.append(Event(_random_time(rng, day), user, "view"))

    for _ in range(n_users // 2):                         # anonymous traffic
        day = yesterday + timedelta(days=rng.randint(-35, 1))
        events.append(Event(_random_time(rng, day), None, "view"))

    return Dataset(users, subscriptions, events)


def _random_subscription(rng: random.Random, sub_id: int, user: str, yesterday: date) -> Subscription:
    product = rng.choice(["pro", "mp"])
    start = yesterday + timedelta(days=rng.randint(-120, 5))
    roll = rng.random()
    if roll < 0.005:
        return Subscription(sub_id, user, product, None, None)                            # NULL start
    if roll < 0.015:
        return Subscription(sub_id, user, product, start, start - timedelta(days=rng.randint(1, 30)))  # inverted
    if roll < 0.035:
        return Subscription(sub_id, user, product, start, start)                          # zero length
    if roll < 0.35:
        return Subscription(sub_id, user, product, start, None)                           # still active
    return Subscription(sub_id, user, product, start, start + timedelta(days=rng.randint(1, 90)))


def _random_time(rng: random.Random, day: date) -> datetime:
    return _at(day, rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59))
