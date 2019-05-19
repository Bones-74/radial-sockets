from time_utils import getDateAndTime

STATE_NOT_ASSIGNED = -1

class PowerStatus(object):
    PWR_OFF_STR = "off"
    PWR_ON_STR  = "on"
    PWR_OFF = 0
    PWR_ON  = 1

    def __init__(self, initial_sts=PWR_OFF):
        self.status = initial_sts

    def __eq__(self, other):
        if isinstance(other, int):
            return self.status == other
        elif isinstance(other, PowerStatus):
            return self.status == other.status

        assert (0)

    def str(self):
        if self.status == self.PWR_OFF:
            return self.PWR_OFF_STR
        elif self.status == self.PWR_ON:
            return self.PWR_ON_STR

        # should never get here
        assert (0)

    @staticmethod
    def ParsePwrSts(pwr_str):
        if pwr_str == PowerStatus.PWR_OFF_STR:
            return PowerStatus.PWR_OFF
        elif pwr_str == PowerStatus.PWR_ON_STR:
            return PowerStatus.PWR_ON

        # should never get here
        assert (0)

    @staticmethod
    def GetStr(status):
        if status == PowerStatus.PWR_OFF:
            return PowerStatus.PWR_OFF_STR
        elif status == PowerStatus.PWR_ON:
            return PowerStatus.PWR_ON_STR

        # should never get here
        assert (0)


class OverrideStatus(object):
    OVR_INACTIVE_STR    = "inactive"
    OVR_SESSION_ON_STR  = "session-on"
    OVR_SESSION_OFF_STR = "session-off"
    OVR_FORCE_ON_STR    = "force-on"
    OVR_FORCE_OFF_STR   = "force-off"
    OVR_ON_UNTIL_STR    = "on-until"
    OVR_OFF_UNTIL_STR   = "off-until"

    OVR_INACTIVE    = 0
    OVR_SESSION_ON  = 1
    OVR_SESSION_OFF = 2
    OVR_FORCE_ON    = 3
    OVR_FORCE_OFF   = 4
    OVR_ON_UNTIL    = 5
    OVR_OFF_UNTIL   = 6

    def __init__(self, initial_sts=OVR_INACTIVE):
        self.status = initial_sts

    def __eq__(self, other):
        if isinstance(other, int):
            return self.status == other
        elif isinstance(other, OverrideStatus):
            return self.status == other.status

        assert (0)

    @staticmethod
    def ParseOvrSts(ovr_str):
        if ovr_str == OverrideStatus.OVR_INACTIVE_STR:
            return OverrideStatus.OVR_INACTIVE
        elif ovr_str == OverrideStatus.OVR_SESSION_ON_STR:
            return OverrideStatus.OVR_SESSION_ON
        elif ovr_str == OverrideStatus.OVR_SESSION_OFF_STR:
            return OverrideStatus.OVR_SESSION_OFF
        elif ovr_str == OverrideStatus.OVR_FORCE_ON_STR:
            return OverrideStatus.OVR_FORCE_ON
        elif ovr_str == OverrideStatus.OVR_FORCE_OFF_STR:
            return OverrideStatus.OVR_FORCE_OFF
        elif ovr_str == OverrideStatus.OVR_ON_UNTIL_ST:
            return OverrideStatus.OVR_ON_UNTILR
        elif ovr_str == OverrideStatus.OVR_OFF_UNTIL_STR:
            return OverrideStatus.OVR_OFF_UNTIL

        # should never get here
        assert (0)

    @staticmethod
    def GetStr(status):
        if status == OverrideStatus.OVR_INACTIVE:
            return OverrideStatus.OVR_INACTIVE_STR
        elif status == OverrideStatus.OVR_SESSION_ON:
            return OverrideStatus.OVR_SESSION_ON_STR
        elif status == OverrideStatus.OVR_SESSION_OFF:
            return OverrideStatus.OVR_SESSION_OFF_STR
        elif status == OverrideStatus.OVR_FORCE_ON:
            return OverrideStatus.OVR_FORCE_ON_STR
        elif status == OverrideStatus.OVR_FORCE_OFF:
            return OverrideStatus.OVR_FORCE_OFF_STR
        elif status == OverrideStatus.OVR_ON_UNTIL:
            return OverrideStatus.OVR_ON_UNTIL_STR
        elif status == OverrideStatus.OVR_OFF_UNTIL:
            return OverrideStatus.OVR_OFF_UNTIL_STR

        # should never get here
        assert (0)

    @staticmethod
    def GetOvrs():
        ovr_dict = {}
        ovr_dict[0] = OverrideStatus.OVR_INACTIVE_STR
        ovr_dict[1] = OverrideStatus.OVR_SESSION_ON_STR
        ovr_dict[2] = OverrideStatus.OVR_SESSION_OFF_STR
        ovr_dict[3] = OverrideStatus.OVR_FORCE_ON_STR
        ovr_dict[4] = OverrideStatus.OVR_FORCE_OFF_STR
        ovr_dict[5] = OverrideStatus.OVR_ON_UNTIL_STR
        ovr_dict[6] = OverrideStatus.OVR_OFF_UNTIL_STR

        return ovr_dict

class SocketStatus(object):
    def __init__(self, name, state=STATE_NOT_ASSIGNED, auto_sts=PowerStatus.PWR_OFF, ovr_sts=OverrideStatus.OVR_INACTIVE, ovr_sess_state=STATE_NOT_ASSIGNED, ovr_t_until=None):
        self.name = name
        self.actual_pwr = PowerStatus.PWR_OFF
        self.last_pwr_state = state
        self.last_auto_sts = auto_sts
        self.ovr_sts = ovr_sts
        self.ovr_session_state = ovr_sess_state
        self.ovr_t_until = ovr_t_until
        self.sts_ovr_on = False
        self.sts_auto_on = False

        self.history = dict()
        self.history ["pwr"] = dict()
        self.history ["ovr"] = dict()
        self.history ["man"] = dict()

    def clone(self):
        skt_sts_ = SocketStatus (self.name,
                                self.last_pwr_state,
                                self.last_auto_sts,
                                self.ovr_sts,
                                self.ovr_session_state,
                                self.ovr_t_until)
        skt_sts_.sts_ovr_on = self.sts_ovr_on
        skt_sts_.sts_auto_on = self.sts_auto_on
        skt_sts_.actual_pwr = self.actual_pwr
        skt_sts_.calcd_auto_sts = self.calcd_auto_sts
        skt_sts_.calcd_state = self.calcd_state
        return skt_sts_

    @staticmethod
    def parse_socket_status (skt_name, status_txt):
        last_pwr_state = 0
        auto_status = PowerStatus.PWR_OFF
        override_status = OverrideStatus.OVR_INACTIVE
        override_session_state = 0
        ovr_t_until = None
        for line in status_txt:
            line_parts = line.split()
            if line_parts[0].strip() == 'state':
                last_pwr_state = int(line_parts[1].strip())
            elif line_parts[0].strip() == 'auto-status':
                auto_status = PowerStatus.ParsePwrSts(line_parts[1].strip())
            elif line_parts[0].strip() == 'override-status':
                override_status = int(OverrideStatus.ParseOvrSts(line_parts[1].strip()))
            elif line_parts[0].strip() == 'override-t-until':
                ovr_t_until = getDateAndTime(line_parts[1].strip())
            elif line_parts[0].strip() == 'override-session-state':
                override_session_state = int(line_parts[1].strip())
        skt = SocketStatus(skt_name, last_pwr_state, auto_status, override_status, override_session_state, ovr_t_until)
        return skt

    def add_states (self, states):
        self.states = states


class Status(object):
    def __init__(self):
        self.sockets = {}

    def clone(self):
        sts_ = Status()
        for _skt_name, skt in self.sockets.items():
            sts_.add_socket(skt.clone())

        return sts_

    def add_socket (self, new_socket):
        self.sockets[new_socket.name] = new_socket

    @staticmethod
    def parse_status_info(status_arr):
        FIND_SOCKET = 0
        GET_SOCKET = 1

        status = Status()
        state = FIND_SOCKET
        for line in status_arr:
            if line.strip() and line.strip()[0] == '#':
                # this is a comment, just move on to next line
                continue

            if state == FIND_SOCKET:
                if line.strip():
                    skt_name = line.strip()
                    skt_sts_txt = []
                    state = GET_SOCKET
            elif state == GET_SOCKET:
                if line.strip() == '{':
                    pass
                elif line.strip() == '}':
                    skt_sts = SocketStatus.parse_socket_status(skt_name, skt_sts_txt)
                    status.add_socket(skt_sts)
                    state = FIND_SOCKET
                else:
                    skt_sts_txt.append(line.strip())
        return status


    def write_file(self, filename):
        # backup_fn = filename + ".bak"
        # shutil.move(filename, 'b.kml')
        with open(filename, "w") as fp:
            for _socket_name, socket in self.sockets.items():
                fp.write(socket.name)
                fp.write("\n")
                fp.write("{\n")
                fp.write("  state {}\n".format(socket.calcd_state))
                fp.write("  # [on/off]\n")
                fp.write("  auto-status  {}\n".format(PowerStatus.GetStr(socket.calcd_auto_sts)))
                fp.write("  # [inactive, session-on, session-off, force-on, force-off]\n")
                fp.write("  override-status {}\n".format(OverrideStatus.GetStr(socket.ovr_sts)))
                fp.write("  # [inactive, session-on, session-off, force-on, force-off]\n")
                fp.write("  override-session-state {}\n".format(socket.ovr_session_state))
                fp.write("  # [hh:mm, dd/MM@hh:mm, dd/MM/YYYY@hh:mm]\n")
                #if 
                fp.write("  override-t-until {}\n".format(socket.ovr_t_until))
                fp.write("}\n")
                fp.write("\n")
            pass
        pass


