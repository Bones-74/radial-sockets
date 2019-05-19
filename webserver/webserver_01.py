from flask import Flask, render_template, request, redirect, url_for
import datetime

from print_utils import print_day, print_days
from config import Board
from boards.SimBoard import SimBoard
from status import PowerStatus, OverrideStatus

web_svr = Flask(__name__)


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
    return render_template('table.html',
                           table_rows=table_rows,
                           control=relay_control,
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

@web_svr.route('/socket_info/<string:socket_name>',methods = ['GET'])
def socket_info(socket_name):
#    if request.method == 'POST':
#        _ovr = request.form['nm']


    global relay_config
    global relay_status
    global relay_func
    cfg_clone = relay_config.clone()
    sts_clone = relay_status.clone()

    board_name = cfg_clone.sockets[socket_name].board
    cfg_clone.add_board(Board(board_name,  SimBoard.ModelName(), "/dev/ttyUsb0", 8))

    pdate = datetime.datetime.now()
    on_map,ovr_map = print_day(relay_func, pdate, cfg_clone, sts_clone, socket_name)
    
    start_date = pdate - datetime.timedelta(days = 50)
    end_date = pdate + datetime.timedelta(days = 50)
    #start_date = pdate - datetime.timedelta(days = 1)
    #end_date = pdate + datetime.timedelta(days = 1)
    full_on_map = print_days(relay_func, start_date, end_date, cfg_clone, sts_clone, socket_name)

    sts_clone = relay_status.clone()
    #titles = ["name", "actual_pwr","calcd_auto_sts", "ovr_sts"]
    titles = ["name", "switch-mode", "socket pwr","auto control",  "auto ovr"]
    socket_row = get_table_row(sts_clone, titles, socket_name, "socket_info")
    return render_template('socket_info.html',
                           table_row=socket_row,
                           socket_name=socket_name,
                           control=relay_control,
                           config=cfg_clone,
                           titles = titles,
                           pwr_map=on_map,
                           ovr_map=full_on_map)

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

def get_table_row(status, titles, socket_name, template):
    socket_sts = status.sockets[socket_name]
    for title in titles:
        if title == "name":
            name_cell = '<td><a href="http://localhost:30080/socket_info/{0}">{0}</a></td>'.format(socket_name);

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
                       + '<form action = "http://localhost:30080/override_cmd" method = "post">' \
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


if __name__ == '__main__':
    web_svr.run()