import pytz
from apscheduler.util import astimezone

tz = pytz.timezone('Asia/Tashkent')
print(f"Type of tz: {type(tz)}")
print(f"Is instance of BaseTzInfo: {isinstance(tz, pytz.tzinfo.BaseTzInfo)}")

try:
    res = astimezone(tz)
    print("astimezone success")
except Exception as e:
    print(f"astimezone failed: {e}")

try:
    from tzlocal import get_localzone
    lz = get_localzone()
    print(f"Type of localzone: {type(lz)}")
    astimezone(lz)
    print("astimezone local success")
except Exception as e:
    print(f"astimezone local failed: {e}")
