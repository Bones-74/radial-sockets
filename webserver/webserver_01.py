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

web_svr = Flask(__name__)

#IMAGES_FOLDER = os.path.join('static', 'images')
IMAGES_FOLDER = 'images'
web_svr.config['UPLOAD_FOLDER'] = IMAGES_FOLDER
web_svr.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

SINGLE_DAY_MAP_FN = 'sday'
MULTI_DAY_MAP_FN = 'mday'


host_addr = "192.168.1.127"
#host_addr = "127.0.0.1"
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
        if request.form['submit_button'] == 'Update':
            pass # do something
        elif request.form['submit_button'] == 'Apply':
            pass # do something else
        elif request.form['submit_button'] == 'Cancel':
            pass # do something else
        else:
            pass # unknown

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
                           config=relay_config,
                           state_entry=state_text[0],
                           script_entry= state_text[1],
                           script_onload= state_text[2],
                           m_map=multi_day)

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
    fn_time_lcl_str = time_now_lcl.strftime("%Y%m%d")

    skt_mday_base = "{}_{}_{}".format(fn_time_lcl_str, socket_name, MULTI_DAY_MAP_FN)
    multi_day = os.path.join(web_svr.config['UPLOAD_FOLDER'], skt_mday_base)
    multi_day_fullbase = os.path.join(web_svr.root_path, 'static', multi_day)
    multi_day_full = os.path.join(web_svr.root_path, 'static', multi_day + ".png")

    board_name = cfg_clone.sockets[socket_name].control_pwr.board
    cfg_clone.add_board(Board(board_name,  SimBoard.ModelName(), "/dev/ttyUsb0", 8))

    start_date = time_now_lcl - datetime.timedelta(days = 100)
    end_date = time_now_lcl + datetime.timedelta(days = 100)

    mday_base_file = Path(multi_day_full)
    if not mday_base_file.exists():
        print_days_image(multi_day_full, start_date, end_date, cfg_clone, socket_name, day_height=2)

    multi_day_full_ovrlay = multi_day_fullbase + "_overlay.png"
    multi_day = multi_day + "_overlay.png"
    overlay_current_day(multi_day_full, multi_day_full_ovrlay, start_date, end_date, cfg_clone, socket_name, day_height=2, current_day=time_now_lcl)


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

    return render_template('socket_info.html',
                           time_str=time_now_lcl_str,
                           table_row=socket_row,
                           socket_name=socket_name,
                           suntimes=suntimes,
                           config=relay_config,
                           titles = titles,
                           m_map=multi_day,
                           socket_links=socket_links)
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

def get_tabbox_for_state(cfg, skt_name):
    CHECKED_STR = "checked"
    SELECTED_STR = "selected"
    DISABLED_STR = "disabled"
    EMPTY_STR = ""
    script_onload = ""
    state_params = dict()
    state_params['id'] = "_01"
    state_params['bt_ON'] = CHECKED_STR
    state_params['bt_OFF'] = EMPTY_STR

    state_params['bt_REL'] = EMPTY_STR
    state_params['bt_ABS'] = CHECKED_STR
    state_params['bt_REL_SR'] = EMPTY_STR
    state_params['bt_REL_SS'] = SELECTED_STR
    state_params['bt_ABS_time'] = "09:00"
    state_params['bt_OS_EN'] = EMPTY_STR
    state_params['bt_OS_plus'] = EMPTY_STR
    state_params['bt_OS_minus'] = CHECKED_STR
    state_params['bt_OS_time'] = "00:45"
    state_params['bt_REL_dd_disable'] = EMPTY_STR
    state_params['bt_ABS_time_disable'] = EMPTY_STR
    state_params['bt_OS_plus_disable'] = EMPTY_STR
    state_params['bt_OS_minus_disable'] = EMPTY_STR
    state_params['bt_OS_time_disable'] = EMPTY_STR

    state_params['lim_ACT_EN'] = EMPTY_STR
    state_params['lim_BFR'] = EMPTY_STR
    state_params['lim_AFT'] = CHECKED_STR
    state_params['lim_REL'] = EMPTY_STR
    state_params['lim_ABS'] = CHECKED_STR
    state_params['lim_REL_SR'] = EMPTY_STR
    state_params['lim_REL_SS'] = SELECTED_STR
    state_params['lim_ABS_time'] = "01:00"
    state_params['lim_OS_EN'] = EMPTY_STR
    state_params['lim_OS_plus'] = EMPTY_STR
    state_params['lim_OS_minus'] = CHECKED_STR
    state_params['lim_OS_time'] = "01:45"
    state_params['lim_BFR_disable'] = DISABLED_STR
    state_params['lim_AFT_disable'] = DISABLED_STR
    state_params['lim_REL_disable'] = DISABLED_STR
    state_params['lim_ABS_disable'] = DISABLED_STR
    state_params['lim_REL_dd_disable'] = DISABLED_STR
    state_params['lim_ABS_time_disable'] = DISABLED_STR
    state_params['lim_OS_disable'] = DISABLED_STR
    state_params['lim_OS_plus_disable'] = DISABLED_STR
    state_params['lim_OS_minus_disable'] = DISABLED_STR
    state_params['lim_OS_time_disable'] = DISABLED_STR

    
    
    
    
    html_for_state_X = state_html.format(**state_params)
    script_for_state_X = state_script.format("_01")

    script_onload += "onload{}();".format("_01")
    return (html_for_state_X, script_for_state_X, script_onload)


if __name__ == '__main__':
    web_svr.run()