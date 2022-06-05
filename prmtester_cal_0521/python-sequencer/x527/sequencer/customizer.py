

def init_variables(sequencer):
    try:
        import pypudding
    except ImportError:
        return False
    '''load default GH info into default variables. must be called after load_sequence and clear_variables'''
    gh = pypudding.IPGHStation()
    var = sequencer.sequence.variables
    product = gh[pypudding.IP_PRODUCT]
    var['factory_name'] = gh[pypudding.IP_SITE]
    var['stationName'] = gh[pypudding.IP_STATION_TYPE]
    line_num = gh[pypudding.IP_LINE_NUMBER]
    var['line_number'] = line_num
    loc = gh[pypudding.IP_LOCATION]
    var['line_id'] = loc + '-' + line_num.split('/')[0]
    var['line_name'] = loc + '-' + line_num
    var['station_id'] = gh[pypudding.IP_STATION_ID]
    var['channel'] = str(sequencer.site + 1)
    return True
