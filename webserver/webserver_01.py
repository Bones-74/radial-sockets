from flask import Flask, render_template, request, redirect, url_for
import datetime

from print_utils import print_day

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
from status import OverrideStatus

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
    titles = ["name", "actual_pwr","calcd_auto_sts", "ovr_sts"]
    return render_template('table.html',
                           control=relay_control,
                           config=relay_config,
                           titles = titles,
                           sockets=relay_status.sockets,
                           ovrs=OverrideStatus.GetOvrs())

@web_svr.route('/override_cmd',methods = ['POST'])
def override_cmd():
    if request.method == 'POST':
        global relay_status
        global relay_config
        ovr_sel = request.form['ovr_sel']
        skt = request.form['skt_id']
        overrides = dict()
        skt_list = [skt]
        overrides [ovr_sel] = skt_list


        global relay_func
        relay_func (relay_control, relay_config, relay_status, overrides)


    return redirect(url_for('index'))

@web_svr.route('/socket_info/<string:socket_name>',methods = ['GET'])
def socket_info(socket_name):
#    if request.method == 'POST':
#        _ovr = request.form['nm']


    global relay_config
    global relay_status
    global relay_func
    cfg_clone = relay_config.clone()
    sts_clone = relay_status.clone ()
    pdate = datetime.datetime.now()
    on_map,ovr_map = print_day(relay_func, pdate, cfg_clone, sts_clone, socket_name)

    titles = ["name", "actual_pwr","calcd_auto_sts", "ovr_sts"]
    return render_template('socket_info.html',
                           socket_name=socket_name,
                           control=relay_control,
                           config=cfg_clone,
                           titles = titles,
                           sockets=sts_clone.sockets,
                           ovrs=OverrideStatus.GetOvrs(),
                           pwr_map=on_map,
                           ovr_map=ovr_map)

def webserver_set_config_status (control, config, status, func):
    global relay_control
    global relay_config
    global relay_status
    global relay_func
    relay_func = func
    relay_config = config
    relay_status = status
    relay_control = control

if __name__ == '__main__':
    web_svr.run()