from datetime import date, timedelta


def calculate_success_rate(success_attempts, total_attempts):
    if total_attempts == 0:
        return 0
    return success_attempts / total_attempts


def calculate_next_interval(success_attempts, success_rate):
    base_interval = 1
    growth_factor = 1.7

    standard_interval = base_interval * (growth_factor ** success_attempts)

    # Коэффициент адаптации
    if success_rate >= 0.75:  # высокий успех, увеличиваем интервал
        adjustment_factor = 1 + (success_rate - 0.75) * 2
    elif success_rate < 0.75:  # низкий успех, уменьшаем интервал
        adjustment_factor = 1 - (0.75 - success_rate) * 2
    else:
        adjustment_factor = 1

    next_interval = standard_interval * adjustment_factor
    return next_interval


def calculate_next_review_date(success_attempts, total_attempts):
    success_rate = calculate_success_rate(success_attempts, total_attempts)
    next_interval_days = calculate_next_interval(success_attempts, success_rate)
    next_review_date = date.today() + timedelta(days=next_interval_days)
    if next_review_date <= date.today():
        next_review_date = date.today() + timedelta(days=1)
    return next_review_date
