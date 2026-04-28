from datetime import date, timedelta

import pytest

from bot.services.utils import (
    calculate_next_interval,
    calculate_next_review_date,
    calculate_success_rate,
)


def test_calculate_success_rate_returns_zero_when_attempts_are_zero():
    assert calculate_success_rate(success_attempts=3, total_attempts=0) == 0


def test_calculate_success_rate_returns_fraction():
    assert calculate_success_rate(success_attempts=3, total_attempts=4) == 0.75


@pytest.mark.parametrize(
    "success_attempts, success_rate, expected",
    [
        (1, 0.50, 0.85),
        (1, 0.75, 1.7),
        (1, 1.00, 2.55),
    ],
)
def test_calculate_next_interval_adjusts_by_success_rate(
    success_attempts,
    success_rate,
    expected,
):
    assert calculate_next_interval(success_attempts, success_rate) == pytest.approx(
        expected
    )


def test_calculate_next_review_date_never_returns_today_or_past():
    result = calculate_next_review_date(success_attempts=0, total_attempts=10)

    assert result >= date.today() + timedelta(days=1)
