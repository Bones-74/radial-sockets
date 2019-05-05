
from status import PowerStatus
from boards.ft232h import ada_ft232h
from boards.b01 import B01
from boards.SimBoard import SimBoard
from time_utils import time_now
from activation_time import ActivationTime


class config_kw():
    APP_KW = 'app'
    APP_TIMER_KW = 'update_timer'
    APP_WEBSERVER_PORT = 'webserver_port'
    APP_SOCKET_PORT = 'socket_port'
    APP_LOCATION_COORDS = 'location'

    BOARD_KW = 'board'
    BOARD_NAME_KW = 'name'
    BOARD_TYPE_KW = 'type'
    BOARD_PORT_KW = 'port'
    BOARD_NUM_CHAN_KW = 'num-chan'

    SOCKET_KW = 'socket'
    SOCKET_NAME_KW = 'name'
    SOCKET_BOARD_KW = 'board'
    SOCKET_CHANNEL_KW = 'channel'

    STATES_KW = 'states'


class App(object):
    APP_SINGLE_RUN_TIMER = 0
    APP_DEFAULT_SOCKET_PORT = 30000
    APP_DEFAULT_WEB_SERVER_PORT = 30080
    APP_MISSING_TXT = "**missing**"
    APP_MISSING_VALUE = -1
    def __init__(self, update_timer, coords, socket_port, webserver_port):
        self.update_timer = update_timer
        self.coords = coords
        self.socket_active = socket_port != App.APP_MISSING_VALUE
        self.socket_port = socket_port
        self.webserver_active = webserver_port != App.APP_MISSING_VALUE
        self.webserver_port = webserver_port


    @staticmethod
    def parse_app (app_def):
        app_timeout = App.APP_MISSING_TXT
        socket_port = App.APP_MISSING_VALUE
        webserver_port = App.APP_MISSING_VALUE
        for line in app_def:
            line_parts = line.split()
            if line_parts[0].strip() == config_kw.APP_TIMER_KW:
                app_timeout = int(line_parts[1].strip())
            if line_parts[0].strip() == config_kw.APP_SOCKET_PORT:
                socket_port = int(line_parts[1].strip())
            if line_parts[0].strip() == config_kw.APP_WEBSERVER_PORT:
                webserver_port = int(line_parts[1].strip())
            if line_parts[0].strip() == config_kw.APP_LOCATION_COORDS:
                coords_str = line_parts[1].strip()
                coords_xy = coords_str.split(":")
                coord_x = float(coords_xy[0])
                coord_y = float(coords_xy[1])
                coords =  {'longitude' : coord_x, 'latitude' : coord_y }

        app = App(app_timeout, coords, socket_port, webserver_port)
        return app


class Board(object):
    BRD_MISSING_TXT = "**missing**"
    def __init__(self, bname, bmodel, bport, num_channels):
        self.name = bname
        self.model = bmodel
        self.port = bport
        self.num_channels = num_channels
        self.board_comms = None
        self.current_status = []

        if self.model == B01.ModelName():
            self.board_comms = B01(bname, bport, num_channels)
        elif self.model == ada_ft232h.ModelName():
            self.board_comms = ada_ft232h(bname, bport, num_channels)
        elif self.model == SimBoard.ModelName():
            self.board_comms = SimBoard(bname, bport, num_channels)

        else:
            pass

    @staticmethod
    def parse_board (board_def):
        brd_name = Board.BRD_MISSING_TXT
        brd_type = Board.BRD_MISSING_TXT
        brd_port = Board.BRD_MISSING_TXT
        brd_chan = Board.BRD_MISSING_TXT
        for line in board_def:
            line_parts = line.split()
            if line_parts[0].strip() == config_kw.BOARD_NAME_KW:
                brd_name = line_parts[1].strip()
            elif line_parts[0].strip() == config_kw.BOARD_TYPE_KW:
                brd_type = line_parts[1].strip()
            elif line_parts[0].strip() == config_kw.BOARD_PORT_KW:
                brd_port = line_parts[1].strip()
            elif line_parts[0].strip() == config_kw.BOARD_NUM_CHAN_KW:
                brd_chan = int(line_parts[1].strip())
        brd = Board(brd_name, brd_type, brd_port, brd_chan)
        return brd

    def update_live_status(self):
        self.current_status = self.board_comms.getCurrentStatus()

    def get_relay_state (self, relay_idx):
        return self.board_comms.getRelay(relay_idx)

    def set_relay_state (self, new_status, relay_idx):
        return self.board_comms.setRelay(new_status, relay_idx)


class Socket(object):
    SKT_MISSING_TXT = "**missing**"
    SKT_MISSING_INT = -1

    def __init__(self, name, board, channel):
        self.name = name
        self.board = board
        self.channel = channel

        #self.current_state = STATE_NOT_ASSIGNED
        #self.current_pwr_state = STATE_NOT_ASSIGNED

    @staticmethod
    def parse_socket (state_def):
        skt_name = Socket.SKT_MISSING_TXT
        skt_board = Socket.SKT_MISSING_TXT
        skt_channel = Socket.SKT_MISSING_INT
        for line in state_def:
            line_parts = line.split()
            if line_parts[0].strip() == config_kw.SOCKET_NAME_KW:
                skt_name = line_parts[1].strip()
            elif line_parts[0].strip() == config_kw.SOCKET_BOARD_KW:
                skt_board = line_parts[1].strip()
            elif line_parts[0].strip() == config_kw.SOCKET_CHANNEL_KW:
                skt_channel = int(line_parts[1].strip())
        skt = Socket(skt_name, skt_board, skt_channel)
        return skt

    def add_states (self, states):
        self.states = states

    def calc_status(self, skt_status):
        # using the current status of the socket, as read from the status file,
        # and the current date/time, work out which state this socket should
        # be in and wheter it should be on of off

        timenow = time_now()
#        timenow = AssignAsLocalTime(time_now())

        # prepare next state as the last one defined, ie, the one that
        # stretches over midnight into the new day
        next_state = self.states [-1]
        for state in self.states:
            state_start = state.activation_time.activation_time_lcl.time()
            if state_start <= timenow.time():
                next_state = state

        skt_status.calcd_state = next_state.id
        skt_status.calcd_auto_sts = next_state.power_state


class SocketState(object):
    def __init__(self, s_id, power_state, activation_time):
        self.id = int (s_id)
        self.power_state = power_state
        self.activation_time = activation_time

    @staticmethod
    def parse_state (state_id, state_txt):
        # split on the '@'- the first part is the stat id and the power
        # setting and the second is the time to switch to this state
        line_parts = state_txt.split('@')
        if len(line_parts) != 2:
            return None

        # get the state id and power setting
        state_id_and_pwr_parts = line_parts[0].split()
        if len(state_id_and_pwr_parts) == 2:
            state_id = state_id_and_pwr_parts[0].strip()
            power_txt = state_id_and_pwr_parts[1].strip()
        else:
            power_txt = state_id_and_pwr_parts[0]

        # now deal with the time of activations for this state
        try:
            activatation_time = ActivationTime.parse_activation_time(line_parts[1])
        except:
            pass

        if power_txt == PowerStatus.PWR_OFF_STR:
            power_id = PowerStatus.PWR_OFF
        elif power_txt == PowerStatus.PWR_ON_STR:
            power_id = PowerStatus.PWR_ON
        else:
            power_id = None

        ss = SocketState(state_id, power_id, activatation_time)
        return ss

    @staticmethod
    def parse_states (state_def_list):
        states = [None] * len(state_def_list)
        for state_id in range(len(state_def_list)):
            state_def = SocketState.parse_state(state_id, state_def_list[state_id])
            if state_def:
                if state_id != state_def.id:
                    print("WARNING: mismatch in state id progression found!")
                    print("         explicitly indexed state with id \"{}\" should have auto id \"{}\".".format(state_def.id, state_id))
                    print("         Ignoring explicitly listed id and using auto id.")
                    state_def.id = state_id

            states[state_id] = state_def

        return states


class Config(object):
    CONFIG_OK = 0
    CONFIG_ERROR_BOARD_NOT_DEFINED = 1
    CONFIG_ERROR_NO_SOCKETS_DEFINED = 2
    CONFIG_ERROR_BOARD_NAME_NOT_DEFINED = 3
    CONFIG_ERROR_SOCKET_NAME_NOT_DEFINED = 4
    CONFIG_ERROR_SOCKET_BOARD_NOT_DEFINED = 5
    CONFIG_ERROR_SOCKET_CHANNEL_NOT_DEFINED = 6
    CONFIG_ERROR_BOARD_COMMS_LIB_NOT_FOUND = 7
    CONFIG_ERROR_SOCKET_CHANNEL_NUM_OUT_OF_RANGE = 8
    CONFIG_ERROR_SOCKET_STATES_MISSING = 9
    CONFIG_ERROR_SOCKET_STATES_EMPTY = 10
    CONFIG_ERROR_SOCKET_STATE_PWR_INVALID = 11
    CONFIG_ERROR_SOCKET_STATE_BADLY_DEFINED = 12
    CONFIG_ERROR_SOCKET_STATE_ACTIVATION_TIME_INVALID = 13


    def __init__(self):
        self.boards = {}
        self.sockets = {}
        self.app = None

    def add_app (self, app):
        self.app = app

    def add_board (self, new_board):
        self.boards[new_board.name] = new_board

    def add_socket (self, new_socket):
        self.sockets[new_socket.name] = new_socket

    def validate(self):
        if len(self.sockets) == 0:
            return self.CONFIG_ERROR_NO_SOCKETS_DEFINED, None

        # check all boards that are referenced are defined
        for brd_name, board in self.boards.items():
            if brd_name is Board.BRD_MISSING_TXT:
                return self.CONFIG_ERROR_BOARD_NAME_NOT_DEFINED, brd_name
            if board.board_comms is None:
                return self.CONFIG_ERROR_BOARD_COMMS_LIB_NOT_FOUND, board.model


        # check socket config for errors
        for skt_name, skt in self.sockets.items():
            if skt_name is Socket.SKT_MISSING_TXT:
                return self.CONFIG_ERROR_SOCKET_NAME_NOT_DEFINED, skt_name
            if skt.name is Socket.SKT_MISSING_TXT:
                return self.CONFIG_ERROR_SOCKET_NAME_NOT_DEFINED, skt_name
            if skt.board is Socket.SKT_MISSING_TXT:
                return self.CONFIG_ERROR_SOCKET_BOARD_NOT_DEFINED, skt_name
            if skt.channel is Socket.SKT_MISSING_TXT:
                return self.CONFIG_ERROR_SOCKET_CHANNEL_NOT_DEFINED, skt_name
            if skt.states is None:
                return self.CONFIG_ERROR_SOCKET_STATES_MISSING, skt_name
            if len(skt.states) == 0:
                return self.CONFIG_ERROR_SOCKET_STATES_EMPTY, skt_name

            # check all boards that are referenced are defined
            if skt.board not in self.boards:
                return self.CONFIG_ERROR_BOARD_NOT_DEFINED, skt.board + " in " + skt_name

            # check that the channel id is within the channel range for the referenced board
            board = self.boards[skt.board]
            if skt.channel < 0 or skt.channel> board.num_channels:
                return self.CONFIG_ERROR_SOCKET_CHANNEL_NUM_OUT_OF_RANGE, "channel {} in {} on {}".format(skt.channel, skt_name, skt.board)

            # check each state definition is correct
            for idx, state in enumerate(skt.states):
                # test that this state is populated with info
                if state is None:
                    return self.CONFIG_ERROR_SOCKET_STATE_BADLY_DEFINED, "state " + str(idx) + " in " + skt_name
                # test that this state has valid power state
                if state.power_state != PowerStatus.PWR_OFF and state.power_state != PowerStatus.PWR_ON:
                    return self.CONFIG_ERROR_SOCKET_STATE_PWR_INVALID, "state " + str(state.id) + " in " + skt_name
                # test that this state has a valid activation time
                if state.activation_time is None:
                    return self.CONFIG_ERROR_SOCKET_STATE_ACTIVATION_TIME_INVALID, "state " + str(state.id) + " in " + skt_name



        return self.CONFIG_OK, None

    @staticmethod
    def parse_config_info(config_arr):
        FIND_TYPE = 0
        GET_BOARD = 1
        GET_SOCKET = 2
        GET_SOCKET_STATES = 3
        GET_APP = 4

        config = Config()
        states = {}

        app_text = []
        board_text = []
        socket_text = []
        state = FIND_TYPE
        for line in config_arr:
            line = line.strip()
            if not line:
                continue

            if line[0] == '#':
                # this is a comment, just move on to next line
                continue

            if state == FIND_TYPE:
                if line == config_kw.BOARD_KW:
                    board_text = []
                    state = GET_BOARD
                elif line == config_kw.SOCKET_KW:
                    socket_text = []
                    states = None
                    state = GET_SOCKET
                elif line == config_kw.APP_KW:
                    app_text = []
                    state = GET_APP
            elif state == GET_BOARD:
                if line == '{':
                    pass
                elif line == '}':
                    board = Board.parse_board(board_text)
                    config.add_board(board)
                    state = FIND_TYPE
                else:
                    board_text.append(line)
            elif state == GET_SOCKET:
                if line == '{':
                    pass
                elif line == '}':
                    socket = Socket.parse_socket(socket_text)
                    socket.add_states(states)
                    config.add_socket(socket)
                    state = FIND_TYPE
                elif line == config_kw.STATES_KW:
                    states_text = []
                    state = GET_SOCKET_STATES
                else:
                    socket_text.append(line)
            elif state == GET_SOCKET_STATES:
                if line == '[':
                    pass
                elif line == ']':
                    states = SocketState.parse_states(states_text)
                    state = GET_SOCKET
                else:
                    states_text.append(line)
            elif state == GET_APP:
                if line == '{':
                    pass
                elif line == '}':
                    app = App.parse_app(app_text)
                    config.add_app(app)
                    state = FIND_TYPE
                else:
                    app_text.append(line)
        return config



