"""
Datetime Utilities
==================

Centralized timezone handling for consistent datetime operations across the application.

All timestamps in the system follow these conventions:
- Storage: Database stores all timestamps in UTC (TIMESTAMPTZ type)
- Display: API responses convert timestamps to Vietnam timezone (UTC+7)
- Format: ISO 8601 with timezone indicator (e.g., "2024-01-15T10:30:45+07:00")

Author: Claude Code
Date: 2025-12-17
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional

from app.core.config import settings

# Timezone constants
UTC = timezone.utc
VIETNAM_TZ = ZoneInfo(settings.DEFAULT_TIMEZONE)  # Asia/Ho_Chi_Minh (UTC+7)


def get_utc_now() -> datetime:
    """
    Get current time in UTC with timezone information.

    Use this instead of datetime.now() to ensure timezone-aware datetimes.

    Returns:
        datetime: Current UTC time (timezone-aware)

    Example:
        >>> get_utc_now()
        datetime.datetime(2024, 1, 15, 3, 30, 45, 123456, tzinfo=datetime.timezone.utc)

        >>> # Instead of:
        >>> datetime.now().isoformat()  # BAD: naive datetime
        >>> # Use:
        >>> get_utc_now().isoformat()  # GOOD: timezone-aware
    """
    return datetime.now(UTC)


def get_vietnam_now() -> datetime:
    """
    Get current time in Vietnam timezone (UTC+7).

    Returns:
        datetime: Current Vietnam time (timezone-aware)

    Example:
        >>> get_vietnam_now()
        datetime.datetime(2024, 1, 15, 10, 30, 45, 123456, tzinfo=ZoneInfo('Asia/Ho_Chi_Minh'))
    """
    return datetime.now(VIETNAM_TZ)


def to_vietnam_time(dt: datetime) -> datetime:
    """
    Convert any datetime to Vietnam timezone (UTC+7).

    If datetime is naive (no timezone), assumes it's UTC.
    This is the primary function for converting timestamps before API responses.

    Args:
        dt: Datetime to convert (can be naive or aware)

    Returns:
        datetime: Datetime in Vietnam timezone (timezone-aware)

    Example:
        >>> # Converting UTC to Vietnam time
        >>> utc_time = datetime(2024, 1, 15, 3, 30, 45, tzinfo=timezone.utc)
        >>> to_vietnam_time(utc_time)
        datetime.datetime(2024, 1, 15, 10, 30, 45, tzinfo=ZoneInfo('Asia/Ho_Chi_Minh'))

        >>> # Naive datetime assumed as UTC
        >>> naive_time = datetime(2024, 1, 15, 3, 30, 45)
        >>> to_vietnam_time(naive_time)
        datetime.datetime(2024, 1, 15, 10, 30, 45, tzinfo=ZoneInfo('Asia/Ho_Chi_Minh'))
    """
    if dt is None:
        return None

    # If naive datetime, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    # Convert to Vietnam timezone
    return dt.astimezone(VIETNAM_TZ)


def to_utc(dt: datetime) -> datetime:
    """
    Convert any datetime to UTC.

    If datetime is naive (no timezone), assumes it's UTC.
    Use this when storing timestamps to database.

    Args:
        dt: Datetime to convert (can be naive or aware)

    Returns:
        datetime: Datetime in UTC (timezone-aware)

    Example:
        >>> # Converting Vietnam time to UTC
        >>> vn_time = datetime(2024, 1, 15, 10, 30, 45, tzinfo=ZoneInfo('Asia/Ho_Chi_Minh'))
        >>> to_utc(vn_time)
        datetime.datetime(2024, 1, 15, 3, 30, 45, tzinfo=datetime.timezone.utc)

        >>> # Naive datetime assumed as UTC
        >>> naive_time = datetime(2024, 1, 15, 3, 30, 45)
        >>> to_utc(naive_time)
        datetime.datetime(2024, 1, 15, 3, 30, 45, tzinfo=datetime.timezone.utc)
    """
    if dt is None:
        return None

    # If naive datetime, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    # Convert to UTC
    return dt.astimezone(UTC)


def format_iso8601(dt: datetime, target_tz: Optional[str] = None) -> str:
    """
    Format datetime as ISO 8601 string with timezone indicator.

    Args:
        dt: Datetime to format (can be naive or aware)
        target_tz: Target timezone ('vietnam' or 'utc'). Defaults to 'vietnam'.

    Returns:
        str: ISO 8601 formatted string with timezone (e.g., "2024-01-15T10:30:45+07:00")

    Example:
        >>> dt = datetime(2024, 1, 15, 3, 30, 45, tzinfo=timezone.utc)
        >>> format_iso8601(dt)
        '2024-01-15T10:30:45+07:00'

        >>> format_iso8601(dt, 'utc')
        '2024-01-15T03:30:45+00:00'

        >>> format_iso8601(dt, 'vietnam')
        '2024-01-15T10:30:45+07:00'
    """
    if dt is None:
        return None

    # Default to Vietnam timezone
    if target_tz is None or target_tz.lower() == 'vietnam':
        dt = to_vietnam_time(dt)
    elif target_tz.lower() == 'utc':
        dt = to_utc(dt)
    else:
        raise ValueError(f"Invalid target_tz: {target_tz}. Use 'vietnam' or 'utc'.")

    # Format as ISO 8601 with timezone
    return dt.isoformat()


def format_iso8601_vietnam(dt: datetime) -> str:
    """
    Format datetime as ISO 8601 string in Vietnam timezone.

    This is the primary function for serializing timestamps in API responses.
    Convenience wrapper for format_iso8601(dt, 'vietnam').

    Args:
        dt: Datetime to format

    Returns:
        str: ISO 8601 formatted string in Vietnam timezone

    Example:
        >>> dt = datetime(2024, 1, 15, 3, 30, 45, tzinfo=timezone.utc)
        >>> format_iso8601_vietnam(dt)
        '2024-01-15T10:30:45+07:00'

        >>> # Usage in Pydantic schema:
        >>> @field_serializer('created_at')
        >>> def serialize_created_at(self, dt: Optional[datetime], _info) -> Optional[str]:
        >>>     return format_iso8601_vietnam(dt)
    """
    return format_iso8601(dt, 'vietnam')


def parse_datetime_string(dt_str: str) -> Optional[datetime]:
    """
    Parse datetime string (ISO format or common formats) into timezone-aware datetime.

    Supports ISO 8601 formats with or without timezone:
    - "2024-01-15T10:30:45+07:00"
    - "2024-01-15T03:30:45Z"
    - "2024-01-15T03:30:45"

    Args:
        dt_str: Datetime string to parse

    Returns:
        datetime: Parsed datetime (timezone-aware)

    Example:
        >>> parse_datetime_string("2024-01-15T10:30:45+07:00")
        datetime.datetime(2024, 1, 15, 10, 30, 45, tzinfo=datetime.timezone(datetime.timedelta(seconds=25200)))

        >>> parse_datetime_string("2024-01-15T03:30:45Z")
        datetime.datetime(2024, 1, 15, 3, 30, 45, tzinfo=datetime.timezone.utc)

        >>> # Naive datetime assumed as UTC
        >>> parse_datetime_string("2024-01-15T03:30:45")
        datetime.datetime(2024, 1, 15, 3, 30, 45, tzinfo=datetime.timezone.utc)
    """
    if not dt_str:
        return None

    try:
        # Try ISO format with timezone
        # Replace 'Z' with '+00:00' for UTC
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))

        # If naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)

        return dt
    except (ValueError, AttributeError):
        return None


# Convenience aliases for common patterns
utc_now = get_utc_now
vietnam_now = get_vietnam_now
to_vn = to_vietnam_time
