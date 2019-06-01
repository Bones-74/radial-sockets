'''
Created on 10 May 2019

@author: root
'''
from datetime import timedelta

#from relay import relay_process
from status import PowerStatus, OverrideStatus
#from config import Board
from control import Control
#from boards.SimBoard import SimBoard
from time_utils import calc_and_activate_test_time, AssignAsLocalTime, ConvertUtcToLocalTime
from Sun import get_sun

import cProfile

def daterange(d1, d2):
    return (d1 + timedelta(days=i) for i in range((d2 - d1).days + 1))


def print_day(date, config, status, socket_name, step=10):
    start_date = date - timedelta(days = 1)
    end_date = date + timedelta(days = 1)

    return print_days(start_date, end_date, config, status, socket_name, step)

def print_days(start_date, end_date, config, _status, socket_name, step=10):
    # get a list of times and on/off transition
    transition_seq = []
    sr_ss_seq = []
    for d in daterange(start_date, end_date):
        sun = get_sun()
        sunrise_lcl = sun.getSunriseTimeLocal(d)
        #sunrise_lcl = ConvertUtcToLocalTime(sunrise['dt'])
        sunset_lcl = sun.getSunsetTimeLocal(d)
        #sunset_lcl = ConvertUtcToLocalTime(sunset['dt'])
        sr_ss_seq.append((d, sunrise_lcl, sunset_lcl))

        socket_cfg = config.sockets[socket_name]
        # Calc the auto-values, ignoring override states
        socket_cfg.reset_state_activation_time()
        socket_cfg.calc_activate_times_for_states(d)
        for state in socket_cfg.states:
            activation_time = state.activation_time.activation_time_lcl
            # if activation_time is None, then this state is not active
            if (activation_time):
                power = state.power_state
                transition_seq.append((activation_time, power))

    # config for printout
    mins_in_day = 60 * 24
    day_width = mins_in_day / step
    last_width_pos = 0
    ON_CHAR = "X"
    OFF_CHAR = "-"

    day_list = []

    # convert list of times into a string
    start_display = False
    last_datetime = None
    last_power_state = PowerStatus.PWR_OFF
    day_map = []
    auto_map = []
    for (act_time, power) in transition_seq:
        if last_datetime is None:
            last_datetime = act_time
            continue

        # see if we/ve gone over a midnight border
        if last_datetime.hour > act_time.hour:
            if start_display:
                # fill in to end of day
                for _ind in range(last_width_pos, day_width):
                    if last_power_state == PowerStatus.PWR_OFF:
                        day_list.append(OFF_CHAR)
                    else:
                        day_list.append(ON_CHAR)

                day_map = ''.join(day_list)
                auto_map.append(''.join(day_map))

                # reset to start of day
                last_width_pos = 0
                day_list = []

            else:
                start_display = True

        if start_display:
            minutes_so_far_today = day_minutes(act_time)
            percentage_of_day = (minutes_so_far_today / (float(mins_in_day)))
            current_width = int(day_width * percentage_of_day)
            for _ind in range(last_width_pos, current_width):
                if last_power_state == PowerStatus.PWR_OFF:
                    day_list.append(OFF_CHAR)
                else:
                    day_list.append(ON_CHAR)

            last_width_pos = current_width

        last_power_state = power
        last_datetime = act_time

    return auto_map


def day_seconds(timenow):
    midnight = timenow.replace(hour=0, minute=0, second=0, microsecond=0)
    return (timenow - midnight).seconds


def day_minutes(timenow):
    seconds = day_seconds(timenow)
    return seconds / 60


def print_days2(relay_process, start_date, end_date, config, status, socket_name, step=10):
    days = []
    count = 0
    for d in daterange(start_date, end_date):
        day_str,_ovr = print_day(relay_process, d, config, status, socket_name, step)
        days.append(day_str)
        count += 1
        #print("{}: {}".format (d.strftime('%Y.%m.%d'), day_str))
    return days

def print_day2(relay_process, date, config, status, socket_name, step=10):
    ON_CHAR = "X"
    OFF_CHAR = "-"
    OVR_CHAR = "O"

    overrides = {}

    day_list = []
    ovr_str = ""
    control = Control()
    control.simulate_run = True
    count_r = 0
    # reset activation times
    config.sockets[socket_name].reset_state_activation_time()
    for hour in range (24):
    #for hour in range (10,11):
        for minute in range (00, 60, step):
            ttime = calc_and_activate_test_time(hour,minute,basedate=date)
            control.time = ttime
            count_r += 1
            #ret_code = relay_process(control, config, status, overrides, socket_name)
            #if ret_code:
            #    exit(ret_code)
            skt_status = status.sockets[socket_name]
            if skt_status.actual_pwr == PowerStatus.PWR_OFF:
                day_list.append(OFF_CHAR)
            else:
                day_list.append(ON_CHAR)
            #if skt_status.ovr_sts == OverrideStatus.OVR_INACTIVE:
            #    ovr_str += OFF_CHAR
            #else:
            #    ovr_str += OVR_CHAR

    day_str = ''.join(day_list)
    return day_str, ovr_str


