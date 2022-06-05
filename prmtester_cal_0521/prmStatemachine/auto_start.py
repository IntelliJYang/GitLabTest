import zmq
import time
import threading
import traceback
from Configure import events
from Configure import zmqports, constant
from Fixture.fixture_client import FixtureHandler, ControlBoard


class AutoStart(threading.Thread):
    def __init__(self, fixture_signal):
        super(AutoStart, self).__init__()
        self._running = True
        self._fixture_signal = fixture_signal
        self.barcode = None  # Barcode()

        # create a socket fo receive msg for fixture_server
        ctx = zmq.Context()
        fixture_sub_address = "tcp://127.0.0.1:{}".format(zmqports.FIXTURE_CTRL_PUB)
        self.fixture_subscriber = ctx.socket(zmq.SUB)
        self.fixture_subscriber.connect(fixture_sub_address)
        self.fixture_subscriber.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
        self._sn_list = []
        self.panel_sn = ""
        self.fixture = ControlBoard()
        self.start()

    def run(self):
        """
        check if fixture engaged,
        :return:
        """
        while self._running:
            try:
                topic, ts, level, origin, data = self.fixture_subscriber.recv_multipart(zmq.NOBLOCK)
                self.received(data)
            except zmq.ZMQError as e:
                pass
            time.sleep(0.1)

        self.fixture_subscriber.setsockopt(zmq.LINGER, 0)
        self.fixture_subscriber.close()

    def stop_serving(self):
        self._running = False

    def received(self, data):
        if not data:
            return
        if FixtureHandler.DOWN_OK in data:
            self._fixture_signal.emit('group_start')
        elif FixtureHandler.RESET_OK in data:
            self._fixture_signal.emit('group_end')
        # elif FixtureHandler.RESET_OK in data:
        #     pass
        # elif FixtureHandler.DOUBLE_START in data:
        #     self._fixture_signal.emit('start_counting')
        # elif FixtureHandler.IN_OK in data:
        #     self.fixture.fixture_down()
        elif FixtureHandler.UP_OK in data:
            self.fixture.fixture_out()
        # elif FixtureHandler.OUT_OK in data:
        #     self._fixture_signal.emit('end_counting')

    def get_e_travelers_list(self):
        _e_travelers = []
        if constant.SIMULATOR_FIXTURE:
            for i in range(constant.GROUPS):
                _e_travelers.append(dict())
                for j in range(constant.SLOTS):
                    _e_travelers[i][str(j)] = {"attributes": {"sn": "{}-{}".format(i, j), "cfg": ""}}
        return _e_travelers

    def camera_on(self):

        # self.panel_sn = "FN68263018PJ42J8J"
        for i in range(2):
            self.panel_sn = self.barcode.run_barcode_client()
            if self.panel_sn:
                break
            else:
                time.sleep(0.5)
                continue
        if self.panel_sn == '':
            return None
            # QMessageBox.critical(QMessageBox(), "Error", "Can not Scan panelsn!")
        return self.panel_sn

    def query_new_sn(self, panel_sn):
        pass
