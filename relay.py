import os
import sys
import argparse
import threading
import time

from config import Config, App
from status import OverrideStatus, SocketStatus, PowerStatus, Status
from time_utils import time_now, getDateAndTime, get_sun, set_location_coords, activate_test_time, deactivate_test_time
from control import Control
#from time import sleep
from webserver.webserver_01 import web_svr, webserver_set_config_status
from Sun import Sun

class relay_exit_codes():
    EXIT_CODE_OK = 0
    EXIT_CODE_ERROR_WITH_CONFIG_FILE = -1
    EXIT_CODE_ERROR_WITH_CONFIG_FILE_MISSING_BOARD = -2
    EXIT_CODE_ERROR_WITH_CONFIG_FILE_MISSING_SOCKET = -3
    EXIT_CODE_ERROR_WITH_CONFIG_FILE_BOARD_DEF = -4
    EXIT_CODE_ERROR_WITH_CONFIG_FILE_SOCKET_DEF = -5
    EXIT_CODE_ERROR_BOARD_COMMS_LIB_MISSING = -6
    EXIT_CODE_ERROR_SOCKET_CHANNEL_NUM_OUT_OF_RANGE = -7
    EXIT_CODE_ERROR_SOCKET_STATES_ERROR = -8
    EXIT_CODE_CMDLINE_ERROR_UNRECOGNISED_SOCKET = -9
    EXIT_CODE_PROCESSING_RELAY_ERROR = -10


def process_args(args=None):
    """Process command line arguments"""
    arg_parser = argparse.ArgumentParser(
        description="Run Relay Configurator.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    arg_parser.add_argument(
        "--config-file",
        help="file to read as the config file")
    arg_parser.add_argument(
        "--status-file",
        help="file to read as the status file")
    arg_parser.add_argument(
        "--override-session-on",
        nargs = '*',
        action='append',
        default=[],
        help="List of sockets to put into session-on override")
    arg_parser.add_argument(
        "--override-session-off",
        nargs = '*',
        action='append',
        help="List of sockets to put into session-off override")
    arg_parser.add_argument(
        "--override-force-on",
        nargs = '*',
        action='append',
        help="List of sockets to put into force-on override")
    arg_parser.add_argument(
        "--override-force-off",
        nargs = '*',
        action='append',
        help="List of sockets to put into force-off override")
    arg_parser.add_argument(
        "--override-off",
        nargs = '*',
        action='append',
        help="List of sockets to put into automatic mode (override off)")
    arg_parser.add_argument(
        "--override-on-until",
        nargs = '*',
        action='append',
        help="A time followed by a list of sockets to keep on until the time is reached")

    arg_parser.add_argument(
        "--override-off-until",
        nargs = '*',
        action='append',
        help="A time followed by a list of sockets to keep off until the time is reached")

    arg_parser.add_argument(
        "--ttime",
        help="time string to be used in testing, expect shortdate pattern: eg, 2009-06-15T13:45:30")

    return arg_parser.parse_args(args=args)


def read_input_files(cfg_fn, sts_fn):
    # read the config and status files
    try:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        full_path = dir_path + '/' + cfg_fn
        with open(full_path) as f:
            config = f.readlines()
        config = [x.strip() for x in config]
    except IOError:
        config = None

    try:
        full_path = dir_path + '/' + sts_fn
        with open(full_path) as f:
            status = f.readlines()
        status = [x.strip() for x in status]
    except IOError:
        status = None

    return config, status


def parse_input_info(cfg_arr, sts_arr):
    # read the config and status files
    if cfg_arr:
        config = Config.parse_config_info(cfg_arr)
    else:
        config = None
    if sts_arr:
        status = Status.parse_status_info(sts_arr)
    else:
        status = None

    return config, status


def retrieve_current_board_statuses(config):

    # retrieve the current board statuses
    assert config.boards
    for _board_name, board in config.boards.items():
        board.update_live_status()


def process_arg_overrides(args):
    overrides = {}
    if args.override_session_on:
        overrides[OverrideStatus.OVR_SESSION_ON_STR] = [item for sublist in args.override_session_on for item in sublist]
    if args.override_session_off:
        overrides[OverrideStatus.OVR_SESSION_OFF_STR] = [item for sublist in args.override_session_off for item in sublist]
    if args.override_force_on:
        overrides[OverrideStatus.OVR_FORCE_ON_STR] = [item for sublist in args.override_force_on for item in sublist]
    if args.override_force_off:
        overrides[OverrideStatus.OVR_FORCE_OFF_STR] = [item for sublist in args.override_force_off for item in sublist]
    if args.override_off:
        overrides[OverrideStatus.OVR_INACTIVE_STR] = [item for sublist in args.override_off for item in sublist]
    if args.override_on_until:
        overrides[OverrideStatus.OVR_ON_UNTIL_STR] = [item for sublist in args.override_on_until for item in sublist]
    if args.override_off_until:
        overrides[OverrideStatus.OVR_OFF_UNTIL_STR] = [item for sublist in args.override_off_until for item in sublist]

    return overrides

def process_overrides(config, status, overrides):
    if OverrideStatus.OVR_INACTIVE_STR in overrides and overrides[OverrideStatus.OVR_INACTIVE_STR]:
        process_override_off(status, overrides[OverrideStatus.OVR_INACTIVE_STR])
    if OverrideStatus.OVR_SESSION_ON_STR in overrides and overrides[OverrideStatus.OVR_SESSION_ON_STR]:
        process_override_session_on(status, overrides[OverrideStatus.OVR_SESSION_ON_STR])
    if OverrideStatus.OVR_SESSION_OFF_STR in overrides and overrides[OverrideStatus.OVR_SESSION_OFF_STR]:
        process_override_session_off(status, overrides[OverrideStatus.OVR_SESSION_OFF_STR])
    if OverrideStatus.OVR_FORCE_ON_STR in overrides and overrides[OverrideStatus.OVR_FORCE_ON_STR]:
        process_override_force_on(status, overrides[OverrideStatus.OVR_FORCE_ON_STR])
    if OverrideStatus.OVR_FORCE_OFF_STR in overrides and overrides[OverrideStatus.OVR_FORCE_OFF_STR]:
        process_override_force_off(status, overrides[OverrideStatus.OVR_FORCE_OFF_STR])
    if OverrideStatus.OVR_ON_UNTIL_STR in overrides and overrides[OverrideStatus.OVR_ON_UNTIL_STR]:
        process_override_on_until(status, overrides[OverrideStatus.OVR_ON_UNTIL_STR])
    if OverrideStatus.OVR_OFF_UNTIL_STR in overrides and overrides[OverrideStatus.OVR_OFF_UNTIL_STR]:
        process_override_off_until(status, overrides[OverrideStatus.OVR_OFF_UNTIL_STR])

def check_and_store_override(socket, new_ovr):
    if socket.ovr_sts != new_ovr:
        # Log the change:
        ovr_history = socket.history["ovr"]
        ovr_history [time_now()] = new_ovr
        socket.ovr_sts = new_ovr

def process_override_off(status, ovr_off):
    for socket_name in ovr_off:
        if socket_name in status.sockets:
            socket = status.sockets[socket_name]
            socket.ovr_session_state = -1
            check_and_store_override(socket, OverrideStatus.OVR_INACTIVE)
        else:
            print ("Cannot find socket {}".format(socket_name))


def process_override_session_on(status, ovr_sess_on):
    for socket_name in ovr_sess_on:
        if socket_name in status.sockets:
            socket = status.sockets[socket_name]
            socket.ovr_session_state = socket.calcd_state
            check_and_store_override(socket, OverrideStatus.OVR_SESSION_ON)
        else:
            print ("Cannot find socket {}".format(socket_name))


def process_override_session_off(status, ovr_sess_off):
    for socket_name in ovr_sess_off:
        if socket_name in status.sockets:
            socket = status.sockets[socket_name]
            socket.ovr_session_state = socket.calcd_state
            check_and_store_override(socket, OverrideStatus.OVR_SESSION_OFF)
        else:
            print ("Cannot find socket {}".format(socket_name))


def process_override_force_on(status, ovr_force_on):
    for socket_name in ovr_force_on:
        if socket_name in status.sockets:
            socket = status.sockets[socket_name]
            socket.ovr_session_state = -1
            check_and_store_override(socket, OverrideStatus.OVR_FORCE_ON)
        else:
            print ("Cannot find socket {}".format(socket_name))


def process_override_force_off(status, ovr_force_off):
    for socket_name in ovr_force_off:
        if socket_name in status.sockets:
            socket = status.sockets[socket_name]
            socket.ovr_session_state = -1
            check_and_store_override(socket, OverrideStatus.OVR_FORCE_OFF)
        else:
            print ("Cannot find socket {}".format(socket_name))


def process_override_on_until(status, ovr_on_until):
    ovr_t_until = None
    for txt in ovr_on_until:
        if txt in status.sockets:
            socket = status.sockets[txt]
            socket.ovr_session_state = -1
            check_and_store_override(socket, OverrideStatus.OVR_ON_UNTIL)
            socket.ovr_t_until = ovr_t_until
        else:
            ovr_t_until = getDateAndTime(txt)
            if ovr_t_until is None:
                print ("Cannot find socket {}".format(txt))


def process_override_off_until(status, ovr_off_until):
    ovr_t_until = None
    for txt in ovr_off_until:
        if txt in status.sockets:
            #MJA:TODO: need to check the time somewhere (maybe not here  and see if the  ocverrdie is valid or not...
            socket = status.sockets[txt]
            socket.ovr_session_state = -1
            check_and_store_override(socket, OverrideStatus.OVR_OFF_UNTIL)
            socket.ovr_t_until = ovr_t_until
        else:
            ovr_t_until = getDateAndTime(txt)
            if ovr_t_until is None:
                print ("Cannot find socket {}".format(txt))


def calculate_next_auto_statuses(control, config, status):
    # calculate the correct auto-statuses
    for socket_name, socket in config.sockets.items():
        if socket_name not in status.sockets:
            new_skt_status = SocketStatus(socket_name, 0, PowerStatus.PWR_OFF, OverrideStatus.OVR_INACTIVE)
            status.sockets[socket_name] = new_skt_status

        skt_sts = status.sockets[socket_name]

        socket.calc_status(skt_sts, control.time)


def send_next_statuses (control, config, status):
    # send calculated power statuses to the board- just write the new
    # value to the board- if it's different it'll change and if the
    # same, well, nothing will happen
    timenow = time_now()
    for socket_name, socket in config.sockets.items():
        skt_sts = status.sockets[socket_name]

        # If there is an override, then adjust the new_pwr_status accordingly
        if skt_sts.ovr_sts == OverrideStatus.OVR_INACTIVE:
            new_pwr_status = skt_sts.calcd_auto_sts

        elif skt_sts.ovr_sts == OverrideStatus.OVR_SESSION_OFF:
            if skt_sts.calcd_state == skt_sts.ovr_session_state:
                new_pwr_status = PowerStatus.PWR_OFF
            else:
                # drop out of session override and use the calcd power state,
                # which is normally the same as the session override
                skt_sts.ovr_sts = OverrideStatus.OVR_INACTIVE
                new_pwr_status = skt_sts.calcd_auto_sts

        elif skt_sts.ovr_sts == OverrideStatus.OVR_SESSION_ON:
            if skt_sts.calcd_state == skt_sts.ovr_session_state:
                new_pwr_status = PowerStatus.PWR_ON
            else:
                # drop out of session override and use the calcd power state,
                # which is normally the same as the session override
                skt_sts.ovr_sts = OverrideStatus.OVR_INACTIVE
                new_pwr_status = skt_sts.calcd_auto_sts

        elif skt_sts.ovr_sts == OverrideStatus.OVR_FORCE_OFF:
            new_pwr_status = PowerStatus.PWR_OFF

        elif skt_sts.ovr_sts == OverrideStatus.OVR_FORCE_ON:
            new_pwr_status = PowerStatus.PWR_ON

        elif skt_sts.ovr_sts == OverrideStatus.OVR_ON_UNTIL:
            if timenow < skt_sts.ovr_t_until:
                new_pwr_status = PowerStatus.PWR_ON
            else:
                new_pwr_status = skt_sts.calcd_auto_sts
                skt_sts.ovr_sts = OverrideStatus.OVR_INACTIVE
                skt_sts.ovr_t_until = None

        elif skt_sts.ovr_sts == OverrideStatus.OVR_OFF_UNTIL:
            if timenow < skt_sts.ovr_t_until:
                new_pwr_status = PowerStatus.PWR_OFF
            else:
                new_pwr_status = skt_sts.calcd_auto_sts
                skt_sts.ovr_sts = OverrideStatus.OVR_INACTIVE
                skt_sts.ovr_t_until = None


        if skt_sts.actual_pwr != new_pwr_status:
            pwr_history = skt_sts.history["pwr"]
            pwr_history[timenow] = new_pwr_status
            skt_sts.actual_pwr = new_pwr_status

        if not control.simulate_run:
            board = config.boards[socket.board]
            board.set_relay_state(new_pwr_status, socket.channel)


sem = threading.Semaphore()
def relay_process(control, config, status, overrides):
    try:
        # grab the semaphore to gaurd shared resource
        sem.acquire()
        # see if this is a simulated run and activate sim_time if true
        if control.simulate_run:
            activate_test_time(control.time)

        control.time = time_now()

        # fill in todays sunrise/sunset details
        sun = get_sun()
        control.sunrise = sun.getSunriseTime(time_now())
        control.sunset = sun.getSunsetTime(time_now())

        # read the current board statuses
        if not control.simulate_run:
            retrieve_current_board_statuses(config)

        # Calc the auto-values, ignoring override states
        calculate_next_auto_statuses(control, config, status)

        if overrides:
            process_overrides(config, status, overrides)

        # Send the next set of values to the boards, taking the overrides into account
        send_next_statuses (control, config, status)

        # re-write the status file
        if control.simulate_run:
            deactivate_test_time()
        else:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            full_path = dir_path + '/' + ".relay-sts"
            status.write_file (full_path)

    except:
        return relay_exit_codes.EXIT_CODE_PROCESSING_RELAY_ERROR
    finally:
        sem.release()

    return relay_exit_codes.EXIT_CODE_OK


def display_validation (validation_res, text, config_file):
    exit_code = relay_exit_codes.EXIT_CODE_OK
    if validation_res == Config.CONFIG_ERROR_BOARD_NOT_DEFINED:
        print("No Boards defined in Config file {} please check and try again".format(config_file))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_WITH_CONFIG_FILE_MISSING_BOARD
    if validation_res == Config.CONFIG_ERROR_BOARD_COMMS_LIB_NOT_FOUND:
        print("Board comms library for {} is missing in config {}. please check and try again".format(text, config_file))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_BOARD_COMMS_LIB_MISSING

    elif validation_res == Config.CONFIG_ERROR_NO_SOCKETS_DEFINED:
        print("No Sockets defined in Config file {} please check and try again".format(config_file))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_WITH_CONFIG_FILE_MISSING_SOCKET
    elif validation_res == Config.CONFIG_ERROR_BOARD_NAME_NOT_DEFINED:
        print("Board is missing a name field (listed as \"{})\"".format(text))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_WITH_CONFIG_FILE_BOARD_DEF
    elif validation_res == Config.CONFIG_ERROR_SOCKET_NAME_NOT_DEFINED:
        print("Socket is missing a name field (listed as \"{})\"".format(text))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_WITH_CONFIG_FILE_SOCKET_DEF
    elif validation_res == Config.CONFIG_ERROR_SOCKET_NAME_NOT_DEFINED:
        print("Socket is missing a name field (listed as \"{})\"".format(text))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_WITH_CONFIG_FILE_SOCKET_DEF
    elif validation_res == Config.CONFIG_ERROR_SOCKET_BOARD_NOT_DEFINED:
        print("Socket is missing a board-name field (listed as \"{})\"".format(text))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_WITH_CONFIG_FILE_SOCKET_DEF
    elif validation_res == Config.CONFIG_ERROR_SOCKET_CHANNEL_NOT_DEFINED:
        print("Socket is missing a channel field (listed as \"{})\"".format(text))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_WITH_CONFIG_FILE_SOCKET_DEF
    elif validation_res == Config.CONFIG_ERROR_SOCKET_CHANNEL_NUM_OUT_OF_RANGE:
        print("Socket channel is out of range for board (\"{})\"".format(text))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_SOCKET_CHANNEL_NUM_OUT_OF_RANGE
    elif validation_res == Config.CONFIG_ERROR_SOCKET_STATES_MISSING:
        print("Socket {} is missing a \"states\" definition".format(text))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_SOCKET_STATES_ERROR
    elif validation_res == Config.CONFIG_ERROR_SOCKET_STATES_EMPTY:
        print("Socket {} has an empty \"states\" definition".format(text))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_SOCKET_STATES_ERROR
    elif validation_res == Config.CONFIG_ERROR_SOCKET_STATE_PWR_INVALID:
        print("{} has an invalid pwr state".format(text))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_SOCKET_STATES_ERROR
    elif validation_res == Config.CONFIG_ERROR_SOCKET_STATE_BADLY_DEFINED:
        print("{} is badly defined. please fix and retry".format(text))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_SOCKET_STATES_ERROR
    elif validation_res == Config.CONFIG_ERROR_SOCKET_STATE_ACTIVATION_TIME_INVALID:
        print("{}: activation state is badly defined. please fix and retry".format(text))
        exit_code = relay_exit_codes.EXIT_CODE_ERROR_SOCKET_STATES_ERROR

    return exit_code


def validate_args(new_ovrrides, config):
    for list_name, arg_list in new_ovrrides.items():
        if arg_list is None:
            continue

        for arg in arg_list:
            if list_name == OverrideStatus.OVR_ON_UNTIL_STR or \
               list_name == OverrideStatus.OVR_OFF_UNTIL_STR:
                ovr_t_until = getDateAndTime(arg)
                if ovr_t_until:
                    continue


            skt = arg
            if skt not in config.sockets:
                text = "{} in cl option {}".format(skt, list_name)
                return relay_exit_codes.EXIT_CODE_CMDLINE_ERROR_UNRECOGNISED_SOCKET, text

    return relay_exit_codes.EXIT_CODE_OK, None


def main__1st_run_from_commandline(args=None,debug_in=None):
    args = process_args(args=args)

    # Either read input files, or use the debug_in which should contain config/status in array of strings
    status_file = None
    if debug_in:
        config_file = "__debug__"
        cfg_arr = debug_in["config"]
        sts_arr = debug_in["status"]
    else:
        config_file = ".relay-cfg"
        if args.config_file:
            config_file = args.config_file

        status_file = ".relay-sts"
        if args.status_file:
            status_file = args.status_file

        cfg_arr, sts_arr = read_input_files(config_file, status_file)

    # Process the input information
    config, status = parse_input_info(cfg_arr, sts_arr)
    if config == None:
        print("Parse issue with Config file {} please check and try again".format(config_file))
        return relay_exit_codes.EXIT_CODE_ERROR_WITH_CONFIG_FILE, None

    validation_res, text = config.validate()
    app_exit_code = display_validation (validation_res, text, config_file)
    if app_exit_code != relay_exit_codes.EXIT_CODE_OK:
        return app_exit_code, None

    if status == None:
        print("Proceeding with no status file (will create at end)")
        # create status structure for each socket
        status = Status()

    # process the override comandline options
    new_overrides = process_arg_overrides(args)

    # Parse commandline options for validity
    validation_res, text = validate_args(new_overrides, config)
    if validation_res == relay_exit_codes.EXIT_CODE_CMDLINE_ERROR_UNRECOGNISED_SOCKET:
        print("Unrecognised socket {} in commandline".format(text))
        return validation_res, None

    # now take the info read from the config and status files and process the info
    control = Control()
    set_location_coords (config.app.coords)
    ret_code = relay_process(control, config, status, new_overrides)
    if ret_code:
        return ret_code

    # re-write the status file
    if status_file:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        full_path = dir_path + '/' + status_file
        status.write_file (full_path)

    # configure & start thread to monitor board inputs
    thread = threading.Thread(target=update_board_inputs,args=(config, status))
    thread.start()

    # Now see if we want to run the app continously
    if config.app:
        if config.app.update_timer != App.APP_SINGLE_RUN_TIMER:
            # Now see if we want to run up the web server and or the socket
            if config.app.socket_active:
                # Start the socket used for controlling the app
                pass
            if config.app.webserver_active:
                # Start the webserver used for controlling the app
                #thread = threading.Thread(target=websrv_01.run, kwargs={'port': config.app.webserver_port,'debug': True})
                webserver_set_config_status(control, config, status, relay_process)
                thread = threading.Thread(target=web_svr.run, kwargs={'port': config.app.webserver_port})
                thread.start()
                pass

            # schedule a timer to kick the logic processing
            control.schedule_run(config.app.update_timer)
            # configure & start thread
            thread = threading.Thread(target=main__run_from_scheduler,args=(control, config, status))
            thread.start()

    return relay_exit_codes.EXIT_CODE_OK

def main__run_from_scheduler(control, config, status):
    while not control.exit_now:
        control.run_event.wait()

        # now take the info read from the config and status files and process the info
        ret_code = relay_process(control, config, status, None)
        if ret_code:
            exit(ret_code)

        control.run_event.clear()

    return err_code

def update_board_inputs(config, status):
    while True:
        for _board_name, board in config.boards.items():
            board.update_live_status()

        for skt_name, skt in config.sockets.items():
            if skt.mon_ovr_on:
                # test the channel to see if this is set
                board = config.boards[skt.mon_ovr_on.board]
                active = board.get_relay_state(skt.mon_ovr_on.channel)
                status.sockets[skt_name].sts_ovr_on = active
            if skt.mon_auto_on:
                # test the channel to see if this is set
                board = config.boards[skt.mon_auto_on.board]
                active = board.get_relay_state(skt.mon_auto_on.channel)
                status.sockets[skt_name].sts_auto_on = active

        time.sleep(2)


if __name__ == "__main__":
    err_code = main__1st_run_from_commandline(args=sys.argv[1:])
    print ("exit({})".format(err_code))
