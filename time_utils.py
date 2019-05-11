import pytz
import datetime
import time

from Sun import Sun

location_coords = {'longitude' : -1.82, 'latitude' : 52.9 }

testing_time = None
def calc_test_time(ttime_hrs,ttime_mins, basedate=None):
    try:
        if basedate:
            timenow = basedate
        else:
            timenow = datetime.datetime.now()
        ttime = timenow.replace(hour=ttime_hrs, minute=ttime_mins, second=0, microsecond=0)
    except ValueError:
        ttime = None

    return ttime

def activate_test_time(ttime):
    global testing_time

    testing_time = ttime

def calc_and_activate_test_time(ttime_hrs,ttime_mins, basedate=None):
    global testing_time

    try:
        if basedate:
            timenow = basedate
        else:
            timenow = datetime.datetime.now()
        testing_time = timenow.replace(hour=ttime_hrs, minute=ttime_mins, second=0, microsecond=0)
    except ValueError:
        testing_time = None

    return testing_time

def deactivate_test_time():
    global testing_time

    testing_time = None

def time_now():
    if testing_time:
        return AssignAsLocalTime(testing_time)
    else:
        return AssignAsLocalTime(datetime.datetime.now())


def set_location_coords(coords):
    global location_coords
    location_coords = coords

def get_sun():
    return Sun(location_coords)


def AssignAsLocalTime(dt_lcl):
    local_tz = pytz.timezone ("Europe/London")
    return local_tz.localize(dt_lcl)


def ConvertToLocalTime(dt_utc):
    local_tz = pytz.timezone ("Europe/London")
    utc_tz = pytz.timezone ("Etc/UTC")
    dt_utc = utc_tz.localize(dt_utc)
    return dt_utc.astimezone(local_tz)


def intTryParse(value):
    try:
        return int(value), True
    except ValueError:
        return value, False


def ParseSimpleTime(HH_mm_str, enforce_strict=False):
    if HH_mm_str[0] == "-":
        HH_mm_str = HH_mm_str[1:]
    h_m = HH_mm_str.split(":")
    hours, hrs_ok = intTryParse(h_m[0])
    if len(h_m) > 1:
        mins,  mins_ok = intTryParse(h_m[1])
    else:
        mins_ok = False

    if hrs_ok and mins_ok:
        if enforce_strict:
            if hours > 23 or hours < 0:
                # hours cannot exceed 0-23
                hrs_ok = False
            if mins > 59 or mins < 0:
                # mins cannot exceed 0-59
                mins_ok = False

    if hrs_ok and mins_ok:
            return (True, hours, mins)
    else:
        return (False, None, None)


def getDateAndTime(txt):
    now = time_now()
    try:
        # today until say, '01:33'
        dt_obj = time.strptime(txt, '%H:%M')
        d_t = now.replace(hour=dt_obj.tm_hour, minute=dt_obj.tm_min, second=0, microsecond=0)
    except:
        try:
            # until say, day/month this year '31/12@01:33'
            dt_obj = time.strptime(txt, '%d/%m@%H:%M')
            d_t = now.replace(month=dt_obj.tm_mon, day=dt_obj.tm_mday, hour=dt_obj.tm_hour, minute=dt_obj.tm_min, second=0, microsecond=0)
        except:
            try:
                # until say, day/month/year time '31/12/2018@01:33'
                dt_obj = time.strptime(txt, '%d/%m/%Y@%H:%M')
                d_t = now.replace(year=dt_obj.tm_year, month=dt_obj.tm_mon, day=dt_obj.tm_mday, hour=dt_obj.tm_hour, minute=dt_obj.tm_min, second=0, microsecond=0)
            except:
                d_t = None
    return d_t


