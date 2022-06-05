import json
import os

config_dir = os.path.expanduser('~/testerconfig')
config_file = os.path.join(config_dir, 'zmqports.json')
f = open(config_file, 'rU')
config = json.load(f)
f.close()

PUB_PORT = config["PUB_PORT"]  # this is our magic number between a server port and a publisher port
PUB_CHANNEL = str(config["PUB_CHANNEL"])
TEST_ENGINE_PORT = config["TEST_ENGINE_PORT"]
TEST_ENGINE_PUB = config["TEST_ENGINE_PUB"]
SEQUENCER_PORT = config["SEQUENCER_PORT"]
SEQUENCER_PUB = config["SEQUENCER_PUB"]

SEQUENCER_PROXY_PUB = config["SEQUENCER_PROXY_PUB"]
SM_PORT = config["SM_PORT"]
SM_PUB = config["SM_PUB"]
SM_RPC_PUB = config["SM_RPC_PUB"]
SM_PROXY_PUB = config["SM_PROXY_PUB"]
FIXTURE_CTRL_PORT = config["FIXTURE_CTRL_PORT"]
FIXTURE_CTRL_PUB = config["FIXTURE_CTRL_PUB"]
LOGGER_PORT = config["LOGGER_PORT"]
LOGGER_PUB = config["LOGGER_PUB"]
UART_PORT = config["UART_PORT"]
UART_PUB = config["UART_PUB"]
UART2_PORT = config["UART2_PORT"]
UART2_PUB = config["UART2_PUB"]
UART3_PORT = config["UART3_PORT"]
UART3_PUB = config["UART3_PUB"]

DATALOGGER_PORT = config["DATALOGGER_PORT"]
DATALOGGER_PUB = config["DATALOGGER_PUB"]
DIGITIZER_PORT = config["DIGITIZER_PORT"]
DIGITIZER_PUB = config["DIGITIZER_PUB"]

ARM_PORT = config["ARM_PORT"]
ARM_PUB = config["ARM_PUB"]

DCSD_PORT = config["DCSD_PORT"]
DCSD_PUB = config["DCSD_PUB"]
LOG_PATH_PORT = config["LOG_PATH_PORT"]

AUDIO_PUB = config["AUDIO_PUB"]
SPDIF_PUB = config["SPDIF_PUB"]
HDMI_PUB = config["HDMI_PUB"]
PWR_SEQUENCER_PUB = config["PWR_SEQUENCER_PUB"]
BKLT_PUB = config["BKLT_PUB"]
B2PCLI_PORT = config["B2PCLI_PORT"]
B2PCLI_PUB = config["B2PCLI_PUB"]

PARSE_PORT = config["PARSE_PORT"]
PARSE_PUB = config["PARSE_PUB"]
