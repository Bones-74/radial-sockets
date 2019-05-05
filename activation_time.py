import datetime


from Sun import Sun
from time_utils import time_now, ParseSimpleTime

SUNRISE_STR = 'sr'
SUNSET_STR = 'ss'

class ActivationTime(object):
    def __init__(self, basetime, floor, ceiling):


        base_t = self.convert_to_local_time(basetime ["base"], basetime ["mod"], basetime ["rand"])
        ceil_t = 0
        floor_t = 0
        if ceiling is not None:
            ceil_t = self.convert_to_local_time(ceiling ["base"], ceiling ["mod"], ceiling ["rand"])
        if floor is not None:
            floor_t = self.convert_to_local_time(floor ["base"], floor ["mod"], floor ["rand"])

        self.activation_time_lcl = base_t
        if floor_t:
            if base_t < floor_t:
                self.activation_time_lcl = floor_t
        elif ceil_t:
            if base_t > ceil_t:
                self.activation_time_lcl = ceil_t
        pass


    def convert_to_local_time(self, basetime, modifier, rand):
        now = time_now()
        sun = Sun()
        coords = {'longitude' : -1.82, 'latitude' : 52.9 }

        if basetime.strip() == SUNSET_STR:
            ss_time = sun.getSunsetTime(coords, date=now)
            hours = ss_time['dt'].hour
            minutes = ss_time['dt'].minute
            self.basetime = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

        elif basetime.strip() == SUNRISE_STR:
            ss_time = sun.getSunriseTime(coords, date=now)
            hours = ss_time['dt'].hour
            minutes = ss_time['dt'].minute
            self.basetime = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

        else:
            (parse_ok, hours,mins) = ParseSimpleTime(basetime,enforce_strict=True)
            if parse_ok:
                self.basetime = now.replace(hour=hours, minute=mins, second=0, microsecond=0)
#                self.basetime = datetime.timedelta(0, minutes=mins, hours=hours)
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
            time_lcl = self.basetime - self.modifier
        else:
            time_lcl = self.basetime + self.modifier

        return time_lcl


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


