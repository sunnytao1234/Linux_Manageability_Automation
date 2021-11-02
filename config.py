# All config needs written here!
from pathlib import Path
import platform
import sys
from Common.file_operator import YamlHandler


# OS
OS_Windows = "Windows"
OS_Linux = 'Linux'

# Get OS Type
OSType: str = OS_Windows if 'WINDOWS' in platform.platform().upper() else OS_Linux

# PATH
BASE_DIR = Path(sys.argv[0]).resolve().parent
BASE_PATH_TEST_DATA = BASE_DIR / "Test_Data"
BASE_PATH_TEST_SCRIPT = BASE_DIR / "Test_Script"
BASE_PATH_TEST_UTILITY = BASE_DIR / "Test_Utility"
BASE_PATH_TEST_SUITE = BASE_DIR / "Test_Suite"
BASE_PATH_TEST_REPORT = BASE_DIR / "Test_Report"
BASE_FILE_GLOBAL_CONFIG = BASE_PATH_TEST_DATA / "global_config.yaml"
PATH_TS_COMMON = BASE_PATH_TEST_SCRIPT / "ts_common"
PATH_TEMP = BASE_DIR / "temp"
PATH_ADDITIONAL = BASE_PATH_TEST_DATA / "additional.yml"
# Debug Log Path
PATH_DEBUG_LOG = BASE_DIR / "debug.log"
# Additional Parameter
GlobalConfig: YamlHandler = YamlHandler(str(BASE_FILE_GLOBAL_CONFIG.absolute()))

# Time Sleep Fibonacci
INT_1 = 1
INT_2 = 2
INT_3 = 3
INT_5 = 5
INT_8 = 8
INT_13 = 13
INT_21 = 21
INT_34 = 34
INT_55 = 55
INT_89 = 89

"""
# Copy to the upper level and run
eg.
if __name__ == '__main__':
    # get log_level
    print(GlobalConfig.log.log_level.value)
"""
