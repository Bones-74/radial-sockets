from flask import Flask, render_template, request, redirect, url_for
import datetime
import os
from pathlib import Path

from print_utils import print_days_image, overlay_current_day
from time_utils import time_now, ConvertUtcToLocalTime
from config import Board
from boards.SimBoard import SimBoard
from status import PowerStatus, OverrideStatus
from Sun import get_sun
from .state_html_def import state_html, state_script
from activation_time import ActivationTime
from config import SocketState

web_svr = Flask(__name__)

#IMAGES_FOLDER = os.path.join('static', 'images')
IMAGES_FOLDER = 'images'
web_svr.config['UPLOAD_FOLDER'] = IMAGES_FOLDER
web_svr.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

SINGLE_DAY_MAP_FN = 'sday'
MULTI_DAY_MAP_FN = 'mday'


host_addr = "192.168.1.127"
#host_addr = "127.0.0.1"
#host_addr = "*"
host_port = "30080"
websvr = "{}:{}".format(host_addr, host_port)

'''
class relay_webserver(Flask):
    def __init__(self, name):
        super(name)

    @web_svr.route('/')
    def hello_world(self):
        return 'Hello World'

    @web_svr.route('/table_test')
    def index(self):
        for _key,_value in self.config.items():
            pass
        return render_template('table.html', name="arshole")

    def set_config_status (self, config, status):
        self.config = config
        self.status = status
'''
relay_control = None
relay_config = None
relay_status = None
relay_func = None

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    relay_control.exit_now = True

@web_svr.route('/shutdown', methods=['POST', 'GET'])
def shutdown():
    if request.method == 'POST':
        shutdown_server()
        return 'Server shutting down...'

    return render_template('shutdown.html')

@web_svr.route('/')
def hello_world():
    return 'Hello World'

@web_svr.route('/table_test',methods = ['POST', 'GET'])
def index():
    if request.method == 'POST':
        _ovr = request.form['nm']


    global relay_status
    #titles = ["name", "actual_pwr","calcd_auto_sts", "ovr_sts"]
    titles = ["name", "switch-mode", "socket pwr","auto control",  "auto ovr"]
    table_rows = get_table_rows(relay_status, titles, "index")
    sun = get_sun()
    suntimes = (sun.getSunriseTimeLocal(), sun.getSunsetTimeLocal())
    return render_template('table.html',
                           table_rows=table_rows,
                           suntimes=suntimes,
                           config=relay_config,
                           titles = titles)

@web_svr.route('/override_cmd',methods = ['POST'])
def override_cmd():
    if request.method == 'POST':
        global relay_status
        global relay_config
        ovr_sel = request.form['ovr_sel']
        skt = request.form['skt_id']
        source = request.form['source']
        overrides = dict()
        skt_list = [skt]
        overrides [ovr_sel] = skt_list


        global relay_func
        relay_func (relay_control, relay_config, relay_status, overrides)

    #return redirect(url_for('index'))
    if (source == 'socket_info'):
        return redirect(url_for(source, socket_name=skt))
    else:
        return redirect(url_for(source))

@web_svr.route('/socket_info/<string:socket_name>/state',methods = ['GET', 'POST'])
def socket_state_info(socket_name):
    global relay_config
    global relay_status

    cfg_clone = relay_config.clone()
    if request.method == 'POST':
        states = ProcessStates(request.form)
        if 'Apply' in request.form:
            relay_config.sockets[socket_name].invalidate_image()
            skt = relay_config.sockets[socket_name]
            skt.states = states
            skt = cfg_clone.sockets[socket_name]
            skt.states = states
        elif 'Test' in request.form:
            skt = cfg_clone.sockets[socket_name]
            skt.states = states

    elif request.method == 'GET':
        pass

    # Prep the filename of the image generated
    time_now_utc = time_now()
    time_now_lcl = ConvertUtcToLocalTime(time_now_utc)
    fn_time_lcl_str = time_now_lcl.strftime("%Y%m%d")
    skt_mday_base = "{}_{}_{}".format(fn_time_lcl_str, socket_name, MULTI_DAY_MAP_FN)
    multi_day = os.path.join(web_svr.config['UPLOAD_FOLDER'], skt_mday_base)
    multi_day = multi_day + "_state_demo"
    multi_day_full = os.path.join(web_svr.root_path, 'static', multi_day + ".png")
    multi_day = multi_day + ".png"

    # generate the image
    start_date = time_now_lcl - datetime.timedelta(days = 100)
    end_date = time_now_lcl + datetime.timedelta(days = 100)
    print_days_image(multi_day_full, start_date, end_date, cfg_clone, socket_name, day_height=2, strobe=7)

    # get the state html
    state_text = get_tabbox_for_state(cfg_clone, socket_name)

    return render_template('socket_state.html',
                           socket_name=socket_name,
                           socket_cfg=cfg_clone.sockets[socket_name],
                           state_entry=state_text[0],
                           script_entry= state_text[1],
                           script_onload= state_text[2],
                           m_map=multi_day)

def ProcessStates(state_def):
    state_id = 0
    states_dict = dict()
    state_text = ""

    # shouldn't have more than 20 states
    count = 20
    while count:
        count -= 1
        if "tb-state-del{}".format(state_id) in state_def:
            # delete this state- essentially, do'nt bother process it.
            # a pass is good enough here- the 'elif' will not be run
            continue

        if "index{}".format(state_id) not in state_def:
            # index field is empty so ignore this pass
            continue

        if "state-active{}".format(state_id) not in state_def:
            state_text += " disabled |"

        if "bt-on-or-off{}".format(state_id) in state_def:
            if state_def["bt-on-or-off{}".format(state_id)] == "1":
                state_text += " on @"
            else:
                state_text += " off @"

            if state_def["base-abs-or-rel{}".format(state_id)] == "rel":
                state_text += " {}".format(state_def["bt-rel-type{}".format(state_id)])
            else:
                state_text += " {}".format(state_def["base-abs-time{}".format(state_id)])

            if "main-offset-check{}".format(state_id) in state_def:
                if state_def["main-offset-check{}".format(state_id)] == "on":
                    if state_def["base-offset-plus-minus{}".format(state_id)] == "plus":
                        state_text += " + {}".format(state_def["base-offset{}".format(state_id)])
                    else:
                        state_text += " - {}".format(state_def["base-offset{}".format(state_id)])

            # Now process the limitaion side of things
            if "limitation-check{}".format(state_id) in state_def:
                if state_def["ls-before-or-after{}".format(state_id)] == "after":
                    state_text += " if after"
                else:
                    state_text += " if before"

                if state_def["ls-abs-or-rel{}".format(state_id)] == "rel":
                    state_text += " {}".format(state_def["ls-rel-type{}".format(state_id)])
                else:
                    state_text += " {}".format(state_def["ls-abs-time{}".format(state_id)])

                if "ls-offset-check{}".format(state_id) in state_def:
                    if state_def["ls-offset-plus-minus{}".format(state_id)] == "plus":
                        state_text += " + {}".format(state_def["ls-offset{}".format(state_id)])
                    else:
                        state_text += " - {}".format(state_def["ls-offset{}".format(state_id)])


            state_idx = state_def["index{}".format(state_id)]
            states_dict [state_idx] = state_text

        else:
            break;

        state_text = ""
        state_id += 1

    states_text = []
    index = 0
    for count in range(len(states_dict)):
        while str(index) not in states_dict:
            index += 1

        states_text.append(states_dict[str(index)])
        index += 1

    states = SocketState.parse_states(states_text)
    return states

@web_svr.route('/socket_info/<string:socket_name>',methods = ['GET'])
def socket_info(socket_name):
    global relay_config
    global relay_func
    cfg_clone = relay_config.clone()
    #import cProfile
    #pr = cProfile.Profile()
    #pr.enable()

    time_now_utc = time_now()
    time_now_lcl = ConvertUtcToLocalTime(time_now_utc)
    time_now_lcl_str = time_now_lcl.strftime("%Y-%m-%d %H:%M:%S")
    fn_time_lcl_str = time_now_lcl.strftime("%Y%m")

    skt_mday_base = "{}_{}_{}".format(fn_time_lcl_str, socket_name, MULTI_DAY_MAP_FN)
    multi_day = os.path.join(web_svr.config['UPLOAD_FOLDER'], skt_mday_base)
    multi_day_fullbase = os.path.join(web_svr.root_path, 'static', multi_day)
    multi_day_full = os.path.join(web_svr.root_path, 'static', multi_day + ".png")

    board_name = cfg_clone.sockets[socket_name].control_pwr.board
    cfg_clone.add_board(Board(board_name,  SimBoard.ModelName(), "/dev/ttyUsb0", 8))

    start_date = time_now_lcl - datetime.timedelta(days = 100)
    end_date = time_now_lcl + datetime.timedelta(days = 100)

    mday_base_file = Path(multi_day_full)
    if not mday_base_file.exists() or cfg_clone.sockets[socket_name].refresh_image():
        print_days_image(multi_day_full, start_date, end_date, cfg_clone, socket_name, day_height=2)

    multi_day_full_ovrlay = multi_day_fullbase + "_overlay.png"
    multi_day = multi_day + "_overlay.png"
    overlay_current_day(multi_day_full, multi_day_full_ovrlay, start_date, end_date, cfg_clone, socket_name, time_now_lcl, day_height=2)


    sts_clone = relay_status.clone()
    #titles = ["name", "actual_pwr","calcd_auto_sts", "ovr_sts"]
    titles = ["name", "switch-mode", "socket pwr","auto control",  "auto ovr"]
    socket_row = get_table_row(sts_clone, titles, socket_name, "socket_info")
    #pr.disable()
    #pr.print_stats()

    socket_links = get_sockets_in_line (cfg_clone)
    # reset info by cloning the real config again
    cfg_clone = relay_config.clone()
    sun = get_sun()
    suntimes = (sun.getSunriseTimeLocal(), sun.getSunsetTimeLocal())
    state_link = '<a href="http://{1}/socket_info/{0}/state">'.format(socket_name, websvr)

    return render_template('socket_info.html',
                           time_str=time_now_lcl_str,
                           table_row=socket_row,
                           socket_name=socket_name,
                           suntimes=suntimes,
                           config=relay_config,
                           titles = titles,
                           m_map=multi_day,
                           socket_links=socket_links,
                           state_link=state_link)
#                           pwr_map=on_map[0],
#                           ovr_map=full_on_map)

def webserver_set_config_status (control, config, status, func):
    global relay_control
    global relay_config
    global relay_status
    global relay_func
    relay_func = func
    relay_config = config
    relay_status = status
    relay_control = control

def get_table_rows(status, titles, template):
    table_rows = []
    for skt_name, _socket_cfg in status.sockets.items():
        table_row = get_table_row(status, titles, skt_name, template)
        table_rows.append("<tr>")
        table_rows.append(table_row)
        table_rows.append("</tr>")

    table_contents = ''.join(table_rows)
    return table_contents

def get_sockets_in_line(status):
    html_arr = []
    for socket in status.sockets:
        socket_link = '<a href="http://{1}/socket_info/{0}">{0}</a>&nbsp;'.format(socket, websvr)
        html_arr.append(socket_link)

    return ''.join(html_arr)


def get_table_row(status, titles, socket_name, template):
    socket_sts = status.sockets[socket_name]
    for title in titles:
        if title == "name":
            name_cell = '<td><a href="http://{1}/socket_info/{0}">{0}</a></td>'.format(socket_name, websvr);

        elif title == "switch-mode":
            color = ""
            if socket_sts.sts_ovr_on:
                color = 'color="#FF0000"'
                mode = "Manual-ON"
            elif socket_sts.sts_auto_on:
                mode = "PC-control"
            else:
                color = '="#FF0000"'
                mode = "Manual-off"
            sw_mode_cell = "<td {1}>{0}</td>".format(mode, color)

        elif title == "socket pwr":
            bgcolor = ""
            color = ""
            if socket_sts.sts_ovr_on:
                bgcolor = 'bgcolor="#FF0000"'
                pwr = "ON"
            elif socket_sts.sts_auto_on:
                if socket_sts.actual_pwr == PowerStatus.PWR_OFF:
                    color = 'color="#0000FF"'
                    pwr = "off"
                else:
                    bgcolor = 'bgcolor="#FF00FF"'
                    pwr = "ON"
            else:
                color = 'style="color: red;"'
                pwr = "off"
            skt_pwr_cell = "<td {1} {2}>{0}</td>".format(pwr, color, bgcolor)

        elif title == "auto control":
            style = ""
            if socket_sts.ovr_sts != OverrideStatus.OVR_INACTIVE:
                style = 'style="color: red;"'

            if socket_sts.actual_pwr == PowerStatus.PWR_OFF:
                pwr = "off"
            else:
                pwr = "ON"
            auto_cell = "<td {1}>{0}</td>".format(pwr, style)

        elif title == "auto ovr":
            cell_start = '<td>' \
                       + '<form action = "http://{0}/override_cmd" method = "post">'.format(websvr) \
                       + '<input type="hidden" name="skt_id" value={0} />'.format(socket_name) \
                       + '<input type="hidden" name="source" value="{0}" />'.format(template) \
                       + '<select name="ovr_sel" onchange="this.form.submit()" autocomplete="off">'
            cell_end = '</select>' \
                     + '<noscript><input type="submit" value="Submit"></noscript>' \
                     + '</form>' \
                     + '</td>'
            drop_down_options = ""
            for ovr_id,ovr_str in OverrideStatus.GetOvrs().items():
                selected = ""
                if ovr_id == socket_sts.ovr_sts:
                    selected = "selected"
                drop_down_options += "<option {1}>{0}</option>".format(ovr_str, selected)

            auto_ovr_cell = cell_start + drop_down_options + cell_end
        else:
            name_cell = "**UNKNOWN_TITLE: {0}".format(title)

    html_table_row = name_cell \
                   + sw_mode_cell \
                   + skt_pwr_cell \
                   + auto_cell \
                   + auto_ovr_cell
    return html_table_row

CHECKED_STR = "checked"
SELECTED_STR = "selected"
EMPTY_STR = ""
def get_tabbox_for_state(cfg, skt_name):
    socket = cfg.sockets [skt_name]
    script_onload = ""
    html_for_state_X = ""
    script_for_state_X = ""

    # We want to introduce a blank/empty sate for use between the states
    state_id = 0
    for state in socket.states:
#        # add the dummy/empty state
#        state_params = default_state_params()
#        state_params['id'] = state_id
#
#        html_for_state_X += state_html.format(**state_params)
#        script_for_state_X += state_script.format(state_params['id'])
#        script_onload += "onload{}();\n".format(state_params['id'])
#
        # Now add the real state
        state_params = init_state_params()
        state_params['id'] = state_id
        if state.active:
            state_params['active'] = CHECKED_STR

        set_basetime_info (state_params, state)
        set_limitationtime_info (state_params, state)

        html_for_state_X += state_html.format(**state_params)
        script_for_state_X += state_script.format(state_params['id'])
        script_onload += "onload{}();\n".format(state_params['id'])

        state_id = state_id + 1

    # add last dummy/empty state
    state_params = default_state_params()
    state_params['id'] = state_id

    html_for_state_X += state_html.format(**state_params)
    script_for_state_X += state_script.format(state_params['id'])
    script_onload += "onload{}();".format(state_params['id'])

    return (html_for_state_X, script_for_state_X, script_onload)

def default_state_params():
    # set to default valid values
    state_params = init_state_params()
    state_params['bt_ON'] = CHECKED_STR
    state_params['bt_REL'] = CHECKED_STR
    state_params['bt_OS_plus'] = CHECKED_STR
    state_params['lim_BFR'] = CHECKED_STR
    state_params['lim_REL'] = CHECKED_STR
    state_params['lim_OS_plus'] = CHECKED_STR
    return state_params

def init_state_params():
    # init the keys to empty
    state_params = dict()
    state_params['active'] = EMPTY_STR
    state_params['bt_ON'] = EMPTY_STR
    state_params['bt_OFF'] = EMPTY_STR
    state_params['bt_REL'] = EMPTY_STR
    state_params['bt_ABS'] = EMPTY_STR
    state_params['bt_ABS_time'] = "09:00"
    state_params['bt_REL_SR'] = EMPTY_STR
    state_params['bt_REL_SS'] = EMPTY_STR
    state_params['bt_OS_EN'] = EMPTY_STR
    state_params['bt_OS_plus'] = EMPTY_STR
    state_params['bt_OS_minus'] = EMPTY_STR
    state_params['bt_OS_time'] = "00:30"
    state_params['lim_ACT_EN'] = EMPTY_STR
    state_params['lim_BFR'] = EMPTY_STR
    state_params['lim_AFT'] = EMPTY_STR
    state_params['lim_REL'] = EMPTY_STR
    state_params['lim_ABS'] = EMPTY_STR
    state_params['lim_REL_SR'] = EMPTY_STR
    state_params['lim_REL_SS'] = EMPTY_STR
    state_params['lim_ABS_time'] = "01:00"
    state_params['lim_OS_EN'] = EMPTY_STR
    state_params['lim_OS_plus'] = EMPTY_STR
    state_params['lim_OS_minus'] = EMPTY_STR
    state_params['lim_OS_time'] = "01:45"

    return state_params

def set_basetime_info (state_params, state):
    if state.power_state == PowerStatus.PWR_ON:
        state_params['bt_ON'] = CHECKED_STR
    else:
        state_params['bt_OFF'] = CHECKED_STR

    if state.activation_time.basetime['base'] == ActivationTime.SUNRISE_STR or \
       state.activation_time.basetime['base'] == ActivationTime.SUNSET_STR:
        state_params['bt_REL'] = CHECKED_STR
        if state.activation_time.basetime['base'] == ActivationTime.SUNRISE_STR:
            state_params['bt_REL_SR'] = SELECTED_STR
        else:
            state_params['bt_REL_SS'] = SELECTED_STR

    else:
        state_params['bt_ABS'] = CHECKED_STR
        state_params['bt_ABS_time'] = state.activation_time.basetime['base']

    if state.activation_time.basetime['mod']:
        state_params['bt_OS_EN'] = CHECKED_STR
        mod_str =  str(state.activation_time.basetime['mod'])
        if mod_str[0] == '-':
            state_params['bt_OS_minus'] = CHECKED_STR
            time_str = mod_str[1:]
        else:
            state_params['bt_OS_plus'] = CHECKED_STR
            time_str = mod_str

        state_params['bt_OS_time'] = time_str
    else:
        state_params['bt_OS_minus'] = CHECKED_STR

def set_limitationtime_info (state_params, state):
    # See if a limit is active
    if state.activation_time.ceilingtime or \
       state.activation_time.floortime:
        state_params['lim_ACT_EN'] = CHECKED_STR
    else:
        state_params['lim_REL'] = CHECKED_STR
        state_params['lim_OS_minus'] = CHECKED_STR
        return

    # we know that one is active, so set the before/after radio accordingly
    if state.activation_time.ceilingtime:
        state_params['lim_BFR'] = CHECKED_STR
        limittime = state.activation_time.ceilingtime
    else:
        state_params['lim_AFT'] = CHECKED_STR
        limittime = state.activation_time.floortime

    # now set the rest of the panel
    if limittime['base'] == ActivationTime.SUNRISE_STR or \
       limittime['base'] == ActivationTime.SUNSET_STR:
        state_params['lim_REL'] = CHECKED_STR
        if limittime['base'] == ActivationTime.SUNRISE_STR:
            state_params['lim_REL_SR'] = SELECTED_STR
        else:
            state_params['lim_REL_SS'] = SELECTED_STR

    else:
        state_params['lim_ABS'] = CHECKED_STR
        state_params['lim_ABS_time'] = limittime['base']

    if limittime['mod']:
        state_params['lim_OS_EN'] = CHECKED_STR
        mod_str =  str(limittime['mod'])
        if mod_str[0] == '-':
            state_params['lim_OS_minus'] = CHECKED_STR
            time_str = mod_str[1:]
        else:
            state_params['lim_OS_plus'] = CHECKED_STR
            time_str = mod_str

        state_params['lim_OS_time'] = time_str

if __name__ == '__main__':
    web_svr.run()