from datetime import datetime, timezone, timedelta

# Philippine timezone (UTC+8)
PH_TIMEZONE = timezone(timedelta(hours=8))

def now_ph():
    """Get current time in Philippine timezone (UTC+8)"""
    return datetime.now(PH_TIMEZONE)

def now_ph_iso():
    """Get current time in Philippine timezone as ISO string"""
    return now_ph().isoformat()

def utc_to_ph(dt):
    """Convert UTC datetime to Philippine time"""
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(PH_TIMEZONE)

def parse_and_convert_to_ph(timestamp_str):
    """Parse ISO timestamp string and convert to Philippine time"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return utc_to_ph(dt)
    except Exception as e:
        print(f"Error parsing timestamp: {e}")
        return now_ph()

def get_ph_date_range(days):
    """Get date range in Philippine time"""
    end_date = now_ph()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date