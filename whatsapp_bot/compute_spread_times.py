from datetime import datetime, time, timedelta
import logging
from typing import List
from zoneinfo import ZoneInfo
from timezone import TIMEZONE
from datetime import datetime, timedelta
from typing import List, Optional, Tuple


# Oct 1, 2025 00:00, timezone-aware
OCT1 = datetime(2025, 10, 1, 0, 0, tzinfo=ZoneInfo(TIMEZONE))



# Default business hours:
# business_hours[0] = Monday, ..., [6] = Sunday
BUSINESS_HOURS_DEFAULT = [
    (time(8, 0), time(20, 0)),  # Monday
    (time(8, 0), time(20, 0)),  # Tuesday
    (time(8, 0), time(20, 0)),  # Wednesday
    (time(8, 0), time(20, 0)),  # Thursday
    (time(9, 0), time(13, 0)), # Friday
    # (time(0, 0), time(0, 0)),  # Saturday 
    (time(0, 0), time(23, 40)),  # Saturday # DEBUG
    (time(8, 0), time(20, 0)), #  Sunday
]


def business_seconds_since_oct1(dt: datetime, business_hours: list = BUSINESS_HOURS_DEFAULT) -> float:
    """
    Compute business seconds since Oct 1 00:00, given 7 pairs of business hours per weekday.
    business_hours[0] = Monday, ..., [6] = Sunday

    After processing the current day we move `current` to 23:59:59 of the previous day
    (instead of simply subtracting one day from the same time).
    """

    if dt < OCT1:
        raise ValueError("dt must be after Oct 1 00:00")

    total_seconds = 0
    current = dt

    while current >= OCT1:
        wd = current.weekday()  # Monday=0
        start_time, end_time = business_hours[wd]

        t = current.time()

        start_sec = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
        end_sec   = end_time.hour * 3600 + end_time.minute * 60 + end_time.second
        current_sec = t.hour * 3600 + t.minute * 60 + t.second

        # compute seconds added for this day
        if current_sec >= end_sec:
            added_sec = max(0, end_sec - start_sec)
        elif current_sec >= start_sec:
            added_sec = max(0, current_sec - start_sec)
        else:
            added_sec = 0

        total_seconds += added_sec
        
        # print(f"Date: {current.date()}, Added seconds: {added_sec}, Total seconds: {total_seconds}")

        # move to previous day at 23:59:59
        prev_date = (current.date() - timedelta(days=1))
        current = datetime(
            prev_date.year,
            prev_date.month,
            prev_date.day,
            23, 59, 59,
            tzinfo=ZoneInfo(TIMEZONE)
        )

    return total_seconds

    

def convert_business_seconds_since_oct1_to_date(business_seconds: int, business_hours: list = BUSINESS_HOURS_DEFAULT, use_logging = True) -> datetime:
    """
    Convert business seconds since Oct 1 00:00 back to a datetime.
    """
    current = OCT1
    remaining_seconds = business_seconds


    log = logging.debug if use_logging else print

    log(f"Converting business seconds back to date...{ business_seconds }") 

    while remaining_seconds >= 0:
        wd = current.weekday()  # Monday=0
        start_time, end_time = business_hours[wd]

        start_sec = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
        end_sec   = end_time.hour * 3600 + end_time.minute * 60 + end_time.second
        business_day_seconds =  end_sec - start_sec

        if remaining_seconds >= business_day_seconds:
            
            # Move to next day
            remaining_seconds -= business_day_seconds
            log(f"Date: {current.date()}, Consuming full business day seconds: {business_day_seconds}, Remaining seconds before: {remaining_seconds}")
            
            current += timedelta(days=1)
        else:
            # Add the remaining time inside the current business day
            result = datetime(
                current.year,
                current.month,
                current.day,
                start_time.hour,
                start_time.minute,
                start_time.second, 
                tzinfo=ZoneInfo(TIMEZONE)
            ) + timedelta(seconds=remaining_seconds)
            
            log(f"Date: {current.date()}, Consuming remaining seconds: {remaining_seconds}, Result: {result.isoformat()}")
            
            return result
        
    raise Exception("Should not reach here if business_seconds > 0") #DEBUG

    




def test_business_seconds_since_oct1():
    # Define business hours: 9:00–17:00 Mon–Fri, closed Sat–Sun

    business_hours = [
        (time(9, 0), time(17, 0)),  # Monday
        (time(9, 0), time(17, 0)),  # Tuesday
        (time(9, 0), time(17, 0)),  # Wednesday
        (time(9, 0), time(17, 0)),  # Thursday
        (time(9, 0), time(17, 0)),  # Friday
        (time(0, 0), time(0, 0)),   # Saturday
        (time(9, 0), time(17, 0))    # Sunday
    ]

    dt = datetime(2025, 10, 10, 13, 0)  # Oct 1, 1:00 PM
    assert business_seconds_since_oct1(dt, business_hours) == (7 * 8 + 4 )* 3600  # full days thu+fri+mon+tue+wed+thu = 7*8 + 4 hours on fri Oct 10
    assert convert_business_seconds_since_oct1_to_date( business_seconds_since_oct1( dt ) ) == dt
    
    
    

def compute_spread_time_based_on_deadline(start: datetime, deadline: datetime, runs: int = 3) -> Tuple[List[datetime], float]:
    """
    Compute `runs` datetimes evenly spaced between `start` (inclusive) and `deadline` (exclusive)
    based on deadline. Returns a tuple of the list of datetimes and business seconds between runs.
    """
    start_business_seconds = business_seconds_since_oct1(start)
    deadline_business_seconds = business_seconds_since_oct1(deadline)
    
    business_seconds_diff = deadline_business_seconds - start_business_seconds
    business_seconds_diff_between_runs = business_seconds_diff / runs

    times = [
        convert_business_seconds_since_oct1_to_date(
            int(start_business_seconds + business_seconds_diff_between_runs * i)
        )
        for i in range(runs)
    ]

    return times, business_seconds_diff_between_runs


def compute_spread_time_based_on_min_diff(start: datetime, min_diff: timedelta, runs: int = 3) -> List[datetime]:
    """
    Compute `runs` datetimes starting from `start`, spaced by at least `min_diff` business seconds.

    Args:
        start: Starting datetime
        min_diff: Minimum difference between consecutive runs (timedelta)
        runs: Number of datetimes to generate

    Returns:
        List of datetime objects
    """
    # Convert start to business seconds
    start_business_seconds = business_seconds_since_oct1(start)
    
    # Convert min_diff to seconds
    min_diff_seconds = min_diff.total_seconds()

    # Generate the list of business seconds for each run
    business_seconds_list = [
        start_business_seconds + min_diff_seconds * i
        for i in range(runs)
    ]

    # Convert back to datetime objects
    return [
        convert_business_seconds_since_oct1_to_date(int(business_sec))
        for business_sec in business_seconds_list
    ]


def compute_spread_times(
    start: datetime,
    deadline: Optional[datetime] = None,
    min_diff: Optional[timedelta] = None,
    runs: int = 3
) -> List[datetime]:
    """
    Compute spread times between `start` and either `deadline` or using `min_diff`.
    Must provide at least one of `deadline` or `min_diff`.
    """
    if deadline is None and min_diff is None:
        raise ValueError("At least one of `deadline` or `min_diff` must be provided.")

    if deadline is not None:
        times, business_seconds_diff_between_runs = compute_spread_time_based_on_deadline(start, deadline, runs)

        # If min_diff is also provided, validate spacing
        if min_diff is not None:
            min_diff_seconds = min_diff.total_seconds()
            if business_seconds_diff_between_runs < min_diff_seconds:
                raise ValueError(
                    f"Computed spacing between runs ({business_seconds_diff_between_runs}s) "
                    f"is less than min_diff ({min_diff_seconds}s)"
                )

        return times

    # Only min_diff is provided
    return compute_spread_time_based_on_min_diff(start, min_diff, runs)


def test_compute_spread_times1():
    start = datetime(2025, 10, 3, 11, 30, tzinfo=ZoneInfo(TIMEZONE))
    deadline = datetime(2025, 10, 5, 9, 30, tzinfo=ZoneInfo(TIMEZONE))
    runs = 3

    run_times = compute_spread_times(start, deadline=deadline, runs=runs)
    
    # print(run_times)

    assert run_times == [
        datetime(2025, 10, 3, 11, 30, tzinfo=ZoneInfo(TIMEZONE)),
        datetime(2025, 10, 3, 12, 30, tzinfo=ZoneInfo(TIMEZONE)),
        datetime(2025, 10, 5, 8, 30, tzinfo=ZoneInfo(TIMEZONE))
    ]
    
def test_compute_spread_times2():
    start = datetime(2025, 10, 7, 19, 30, tzinfo=ZoneInfo(TIMEZONE))
    min_diff = timedelta(hours=4)
    runs = 2

    run_times = compute_spread_times(start, min_diff=min_diff, runs=runs)
    
    # print(run_times)

    assert run_times == [
        datetime(2025, 10, 7, 19, 30, tzinfo=ZoneInfo(TIMEZONE)),
        datetime(2025, 10, 8, 11, 30, tzinfo=ZoneInfo(TIMEZONE))
    ]
    
def test_compute_spread_times3():
    start = datetime(2025, 10, 7, 19, 30, tzinfo=ZoneInfo(TIMEZONE))
    min_diff = timedelta(hours=4)
    deadline = datetime(2025, 10, 8, 8, 0, tzinfo=ZoneInfo(TIMEZONE))
    runs = 2

    try:
        run_times = compute_spread_times(start, min_diff=min_diff, deadline=deadline, runs=runs)
    except ValueError as e:
        return True
    
    raise Exception("Expected ValueError due to insufficient spacing between runs")
    
    # print(run_times)

    




