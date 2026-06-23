import re
import math


def validate_ip_range(ip_range):
    """Validate an IP address or CIDR notation string.

    Supports:
        - Single IPv4 addresses (e.g., '192.168.1.1')
        - CIDR notation (e.g., '192.168.1.0/24')
        - Hyphenated ranges (e.g., '192.168.1.1-254')

    Args:
        ip_range: String containing the IP or CIDR to validate.

    Returns:
        True if the format is valid, False otherwise.
    """
    if not ip_range or not isinstance(ip_range, str):
        return False

    ip_range = ip_range.strip()

    # Pattern for a single IPv4 octet (0-255)
    octet = r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)'
    ipv4 = rf'{octet}\.{octet}\.{octet}\.{octet}'

    # Single IP address
    single_ip_pattern = rf'^{ipv4}$'
    if re.match(single_ip_pattern, ip_range):
        return True

    # CIDR notation (e.g., 192.168.1.0/24) with prefix length 0-32
    cidr_pattern = rf'^{ipv4}/(?:3[0-2]|[12]?\d)$'
    if re.match(cidr_pattern, ip_range):
        return True

    # Hyphenated range (e.g., 192.168.1.1-254)
    range_pattern = rf'^{ipv4}-(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$'
    if re.match(range_pattern, ip_range):
        return True

    return False


def validate_email(email):
    """Validate an email address format.

    Uses a comprehensive regex pattern that covers standard email formats.

    Args:
        email: String containing the email address to validate.

    Returns:
        True if the email format is valid, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip()

    # RFC 5322 simplified pattern
    pattern = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'

    return bool(re.match(pattern, email))


def paginate_query(query, page, per_page):
    """Apply pagination to a SQLAlchemy query and return structured results.

    Args:
        query: A SQLAlchemy query object.
        page: Page number (1-indexed). Defaults to 1 if invalid.
        per_page: Number of items per page. Clamped to 1-100 range.

    Returns:
        A dictionary with:
            - items: List of serialized model instances (via to_dict()).
            - total: Total number of matching records.
            - pages: Total number of pages.
            - current_page: The current page number.
            - per_page: Items per page.
            - has_next: Whether there is a next page.
            - has_prev: Whether there is a previous page.
    """
    # Sanitize inputs
    try:
        page = max(1, int(page))
    except (TypeError, ValueError):
        page = 1

    try:
        per_page = max(1, min(100, int(per_page)))
    except (TypeError, ValueError):
        per_page = 20

    # Execute paginated query
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
    }


def format_duration(seconds):
    """Convert a duration in seconds to a human-readable string.

    Args:
        seconds: Number of seconds (int or float).

    Returns:
        A human-readable duration string. Examples:
            - 0 -> '0s'
            - 45 -> '45s'
            - 90 -> '1m 30s'
            - 3661 -> '1h 1m 1s'
            - 86400 -> '1d 0h 0m 0s'
    """
    if seconds is None:
        return 'N/A'

    try:
        seconds = float(seconds)
    except (TypeError, ValueError):
        return 'N/A'

    if seconds < 0:
        return 'N/A'

    seconds = int(math.floor(seconds))

    if seconds == 0:
        return '0s'

    days = seconds // 86400
    remaining = seconds % 86400
    hours = remaining // 3600
    remaining = remaining % 3600
    minutes = remaining // 60
    secs = remaining % 60

    parts = []
    if days > 0:
        parts.append(f'{days}d')
    if hours > 0 or days > 0:
        parts.append(f'{hours}h')
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f'{minutes}m')
    parts.append(f'{secs}s')

    return ' '.join(parts)
