from datetime import datetime
import pytz

def get_ist_now():
    """Returns the current datetime in Indian Standard Time (IST)."""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).replace(tzinfo=None) # naive datetime for SQLAlchemy compatibility
