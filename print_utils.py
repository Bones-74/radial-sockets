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
from time_utils import calc_and_activate_test_time

def daterange(d1, d2):
    return (d1 + timedelta(days=i) for i in range((d2 - d1).days + 1))


def print_days(relay_process, start_date, end_date, config, status, socket_name, step=10):
    days = []
    d10 = 0
    d1 = 0
    for d in daterange(start_date, end_date):
        day_str,_ovr = print_day(relay_process, d, config, status, socket_name, step)
        d1 += 1
        if d1 > 10:
            d1 = 0
            d10 += 1
            
        days.append(day_str)
        #print("{}: {}".format (d.strftime('%Y.%m.%d'), day_str))


def print_day(relay_process, date, config, status, socket_name, step=10):
    ON_CHAR = "X"
    OFF_CHAR = "-"
    OVR_CHAR = "O"

    #board_name = "sim"
    #relay_channel_idx = 0
    #skt = Socket(socket_name, board_name, relay_channel_idx)
    overrides = {}
    # add sim board to config
    #config.add_board(Board(board_name,  SimBoard.ModelName(), "/dev/ttyUsb0", 8))

    # ----------------------test-setup-end-----------------------
    #step = 10
    day_str = ""
    ovr_str = ""
    control = Control()
    control.simulate_run = True
    for hour in range (24):
#        calc_and_activate_test_time(hour, 0, basedate=date)
        if hour == 1:
            pass
        #states = SocketState.parse_states(self.states_text)
        #skt.add_states(states)
        #config.add_socket(skt)
        #relay_ch = config.sockets[socket_name].channel

        for minute in range (0, 60, step):
            ttime = calc_and_activate_test_time(hour,minute,basedate=date)
            control.time = ttime
            ret_code = relay_process(control, config, status, overrides)
            if ret_code:
                exit(ret_code)
            skt_status = status.sockets[socket_name]
            if skt_status.actual_pwr == PowerStatus.PWR_OFF:
                day_str += OFF_CHAR
            else:
                day_str += ON_CHAR
            if skt_status.ovr_sts == OverrideStatus.OVR_INACTIVE:
                ovr_str += OFF_CHAR
            else:
                ovr_str += OVR_CHAR

    return day_str, ovr_str


