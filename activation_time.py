import datetime
import pytz

from Sun import get_sun
from time_utils import time_now, ParseSimpleTime, AssignAsLocalTime, ConvertUtcToLocalTime

SUNRISE_STR = 'sr'
SUNSET_STR = 'ss'

class ActivationTime(object):
    reset_time = AssignAsLocalTime(datetime.datetime.min + datetime.timedelta(days=100))
    def __init__(self, basetime, floor, ceiling):

        self.last_activation_time = self.reset_time

        self.basetime = basetime
        self.floortime = floor
        self.ceilingtime = ceiling

        self.update_activation_time (time_now())

        pass

    def clone(self):
        act_time_ = ActivationTime (self.basetime, self.floortime, self.ceilingtime)
        act_time_.last_activation_time = self.last_activation_time
        return act_time_

    def reset_activation_time(self):
        #timezone = pytz.timezone("America/Los_Angeles")
        #start_date = datetime.datetime.min + datetime.timedelta(days = 50)
        self.last_activation_time = self.reset_time

    def update_activation_time(self, timenow):
        update_activation_time = False
        update_time = self.last_activation_time + datetime.timedelta(days=1)
        if update_time < timenow:
            update_activation_time = True
            self.last_activation_time = timenow#

        if update_activation_time:
            base_t = self.convert_to_time(self.basetime, timenow)
            ceil_t = 0
            floor_t = 0
            if self.ceilingtime is not None:
                ceil_t = self.convert_to_time(self.ceilingtime, timenow)
            if self.floortime is not None:
                floor_t = self.convert_to_time(self.floortime, timenow)

            self.activation_time_utc = base_t
            self.activation_time_lcl = ConvertUtcToLocalTime(base_t)
            if floor_t:
                if base_t < floor_t:
                    self.activation_time_utc = None
                    self.activation_time_lcl = None
            elif ceil_t:
                if base_t > ceil_t:
                    self.activation_time_utc = None
                    self.activation_time_lcl = None

        return self.activation_time_utc

#    def convert_to_local_time(self, time_dict, timenow):
    def convert_to_time(self, time_dict, timenow):
        sun = get_sun()

        basetime = time_dict  ["base"]
        modifier = time_dict  ["mod"]
        rand = time_dict  ["rand"]

        if basetime.strip() == SUNSET_STR:
            sunset_lcl = sun.getSunsetTimeLocal(date=timenow)
            sunset_utc = sun.getSunsetTimeUtc(date=timenow)
            basetime_utc = sunset_utc
#            dst_diff = sunset_lcl.dst()
            #sunset_lcl = AssignAsLocalTime(ss_time['dt'])
#            hours = (sunset_lcl + dst_diff).hour
            hours = sunset_lcl.hour
            minutes = sunset_lcl.minute
            basetime_lcl = timenow.replace(hour=hours, minute=minutes, second=0, microsecond=0)
#            self.basetime = timenow.replace(hour=hours, minute=minutes, second=0, microsecond=0)

        elif basetime.strip() == SUNRISE_STR:
            sunrise_lcl = sun.getSunriseTimeLocal(date=timenow)
            sunrise_utc = sun.getSunriseTimeUtc(date=timenow)
            basetime_utc = sunrise_utc
#            dst_diff = sunrise_lcl.dst()
            #sunrise_lcl = AssignAsLocalTime(ss_time['dt'])
#            hours = (sunrise_lcl + dst_diff).hour
            hours = sunrise_lcl.hour
            minutes = sunrise_lcl.minute
            basetime_lcl = timenow.replace(hour=hours, minute=minutes, second=0, microsecond=0)
#            self.basetime = timenow.replace(hour=hours, minute=minutes, second=0, microsecond=0)

        else:
            (parse_ok, hours, mins) = ParseSimpleTime(basetime,enforce_strict=True)
            if parse_ok:
                basetime_lcl = timenow.replace(hour=hours, minute=mins, second=0, microsecond=0)
                basetime_utc = timenow.replace(hour=hours, minute=mins, second=0, microsecond=0)
#                self.basetime = timenow.replace(hour=hours, minute=mins, second=0, microsecond=0)
            else:
                return None
        isNegative = False
        if modifier:
            isNegative = modifier[0] == '-'
            if isNegative:
                modifier = modifier[1:]

            (parse_ok, hours, mins) = ParseSimpleTime(modifier)
            if parse_ok:
                self.modifier = datetime.timedelta(0, minutes=mins, hours=hours)
            else:
                return None
        else:
            self.modifier = datetime.timedelta(0, 0, 0)
        if rand:

            (parse_ok, hours,mins) = ParseSimpleTime(rand)
            if parse_ok:
                self.rand = datetime.timedelta(0, minutes=mins, hours=hours)
            else:
                return None
        else:
            self.rand = datetime.timedelta(0, 0, 0)

        time_lcl = 0
        if isNegative:
            time_lcl = basetime_lcl - self.modifier
        else:
            time_lcl = basetime_lcl + self.modifier

        time_utc = 0
        if isNegative:
            time_utc = basetime_utc - self.modifier
        else:
            time_utc = basetime_utc + self.modifier

        #return time_lcl
        return time_utc


    @staticmethod
    def parse_activation_time (time_txt):
        floor_time = None
        ceiling_time = None
        trans_time_parts = time_txt.split('if')
#        if len(trans_time_parts) != 2:
#            return None

        base_time = ActivationTime.parse_time (trans_time_parts[0])
        if base_time is None:
            return None

        if len(trans_time_parts) == 2:
            state_criteria = trans_time_parts[1].strip()
            if len(state_criteria) > 0:
                # split on 'ter' as in 'af*ter*' to give a 2 element array is text
                floor_text_and_time = state_criteria.split("after")
                if len(floor_text_and_time) == 2:
                    floor_time = ActivationTime.parse_time (floor_text_and_time[1])
                    if floor_time is None:
                        # something is wrong with this state- the floor time is not decodable
                        return None
                else:
                    # split on 'fore' as in 'be*fore*' to give a 2 element array is
                    ceiling_text_and_time = state_criteria.split("before")
                    if len(ceiling_text_and_time) == 2:
                        ceiling_time = ActivationTime.parse_time (ceiling_text_and_time[1])
                        if ceiling_time is None:
                            # something is wrong with this state- ceiling_time is not decodable
                            return None
                    else:
                        # something is wrong with this state- there is something here
                        # but it is not decodable
                        return None

        return ActivationTime(base_time, floor_time, ceiling_time)


    @staticmethod
    def parse_time (time_txt):
        # Deal with the random time part of activation time
        time_and_rnd = time_txt.split("~")
        time_rand = None
        if len(time_and_rnd) == 2:
            time_rand = time_and_rnd[1].strip()

        # Deal with the base and modifer for activation time
        time_and_mod = time_and_rnd[0].split('+')
        time_mod = None
        if len(time_and_mod) == 2:
            time_mod = time_and_mod[1].strip()
        else:
            time_and_mod = time_and_rnd[0].split('-')
            if len(time_and_mod) == 2:
                time_mod = "-" + time_and_mod[1].strip()

        base = time_and_mod[0].strip()
        if not base:
            return None

        # now test each component for correctness before we try and use it
        for time_val_str in (base, time_mod, time_rand):
            if time_val_str == SUNSET_STR or time_val_str == SUNRISE_STR:
                continue
            elif time_val_str:
                (parse_ok, _hrs, _mins) =  ParseSimpleTime(time_val_str, enforce_strict=True)
                if not parse_ok:
                    return None

        return {"base":base, "mod":time_mod, "rand":time_rand}


