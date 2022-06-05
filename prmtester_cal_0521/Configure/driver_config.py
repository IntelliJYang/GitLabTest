import json
import os

# get Configure path , all config should in this folder
config_dir = os.path.split(__file__)[0]

# driver relate config
driver_config_file = os.path.join(config_dir, 'DriverConfig.json')
with open(driver_config_file) as f:
    driver_config = json.load(f)
FIXTURE_CFG = driver_config.get("fixture")
HW_CFG = driver_config.get("HW")

FIXTURE_SERIAL_PORT = FIXTURE_CFG.get("port")

#
# if __name__ == '__main__':
#     print HW_CFG.get('uut0').get('zynq')
