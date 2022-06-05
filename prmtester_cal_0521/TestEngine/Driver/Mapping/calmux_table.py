import os
import json

map_path = os.path.abspath(os.path.dirname(__file__) + '/calmux_map.json')


class MUXTable(object):
    '''
    IOTable     class to parse io config json file
    :param:     profile:     string, file path of the io configuration json file, default None
    :example:
                io_table = IOTable(pin_map, "/mix/hwio.json")
    '''

    def __init__(self, profile=map_path):
        self.io_table = {}
        if profile:
            assert os.path.exists(profile)
            with open(profile, 'r') as f:
                self.io_table = json.load(f)

    def load_from_file(self, path):
        '''
        RPC service function, allow host to request loading a new io config file
        :param:     path:       string, file path of the io configuration json file
        :example for remote call:
                    client.call(io_table_load_hwio, "/mix/hwio/json")
        '''
        assert os.path.exists(path)
        with open(path, 'r') as f:
            self.io_table = json.load(f)
        return '--PASS--'

    def get_by_netname(self, net, sub_net=None, table='relay'):
        '''
        search every sub table(relay_table, measure_table, eeprom_table...) to get the config
        for input net
        :param: net,    string,    main net name,
        :param: sub_net string,    sub net name, can be None
        :param: table   string,    indicate to use which sub_table
        :example:
            config = getby_netname("PP_VCC_BATT", "CONNECT")
        '''
        for name, sub_table in self.io_table.iteritems():
            if table.lower() in name.lower():
                try:
                    config = sub_table[net] if sub_net is None else sub_table[net][sub_net]
                    return config
                except:
                    print('{}-{} is not valid NET name'.format(net, sub_net))
        raise Exception('{}-{} is not valid NET name'.format(net, sub_net))

