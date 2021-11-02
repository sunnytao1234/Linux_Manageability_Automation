import os,re,datetime
from Common.file_operator import YamlOperator
from Common.log import log
from Common.common_function import get_current_dir


class Report:

    @staticmethod
    def get_platform():
        report_path = get_current_dir(r"Test_Data\td_report\linux_report.yml")
        report_result = YamlOperator(report_path).read()
        report_config = report_result.get("platform", "")
        if not report_config:
            log.info("report style not need platform")
            return False
        else:
            log.info("report platform value{}".format(report_config))
            additional_path = get_current_dir(r"Test_Data\additional.yml")
            result = YamlOperator(additional_path).read()
            uut_platform = result.get("platform", "").upper()
            return uut_platform

    @staticmethod
    def get_config():
        report_path = get_current_dir(r"Test_Data\td_report\linux_report.yml")
        report_result = YamlOperator(report_path).read()
        report_config = report_result.get("config","")
        if not report_config:
            log.info("report style not need config")
            return False
        else:
            log.info("report config value{}".format(report_config))
            additional_path = get_current_dir(r"Test_Data\additional.yml")
            result = YamlOperator(additional_path).read()
            uut_config = result.get("config", "").upper()
            return uut_config


    @staticmethod
    def get_set_ID():
        report_path = get_current_dir(r"Test_Data\td_report\linux_report.yml")
        report_result = YamlOperator(report_path).read()
        report_setid = report_result.get("test_set_id", "")
        if not report_setid:
            log.info("report style not need test_set_id")
            return False
        else:
            additional_path = get_current_dir(r"Test_Data\additional.yml")
            result = YamlOperator(additional_path).read()
            test_ID = result.get("test_set_id", "").upper()
            return test_ID

    @staticmethod
    def get_mac_adress():
        report_path = get_current_dir(r"Test_Data\td_report\linux_report.yml")
        report_result = YamlOperator(report_path).read()
        report_mac = report_result.get("uut_mac", "")
        if not report_mac:
            log.info("report style not need uut_mac")
            return False
        else:
            res = os.popen("ipconfig /all").read()
            res = re.findall(r"Ethernet adapter Ethernet.*?:(.*?)NetBIOS over Tcpip", res, re.S)
            print(res)
            res = re.findall(
                r"(?i)Description.*?: (Realtek.*?)\n.*?: (.{2}-.{2}-.{2}-.{2}-.{2}-.{2}).{0,250}?ipv4.{0,100}?(\d{0,3}\.\d{0,3}\.\d{0,3}\.\d{0,3})",
                res[0], re.S)
            print(res)
            assert res != [], "Can't get a usable mac"
            return res[0]

    @staticmethod
    def get_start_time():
        report_path = get_current_dir(r"Test_Data\td_report\linux_report.yml")
        report_result = YamlOperator(report_path).read()
        report_start_time = report_result.get("Timestamp", "")
        if not report_start_time:
            log.info("report style not need Timestamp")
            return False
        else:
            log.info("get the test start run uut time")
            if os.path.exists('time.txt'):
                with open('time.txt') as f:
                    start_time = str(datetime.datetime.strptime(f.read(), '%a %b %d %H:%M:%S %Y')).strip().replace(" ","-").replace(":", "-")
            else:
                log.info("not find time.txt")
            return start_time


    @staticmethod
    def get_testsetpath():
        report_path = get_current_dir(r"Test_Data\td_report\linux_report.yml")
        report_result = YamlOperator(report_path).read()
        report_name = report_result.get("testsetpath", "")
        if not report_name:
            log.info("report style not need testsetpath")
            return False
        else:
            additional_path = get_current_dir(r"Test_Data\additional.yml")
            result = YamlOperator(additional_path).read()
            project_name = result.get("name", "").upper()
            return project_name


    @staticmethod
    def get_email():
        additional_path = get_current_dir(r"Test_Data\additional.yml")
        result = YamlOperator(additional_path).read()
        email = result.get("tester", "").strip()
        return email

    @staticmethod
    def get_report_key_and_value():
        report_path = get_current_dir(r"Test_Data\td_report\linux_report.yml")
        report_result = YamlOperator(report_path).read()
        report_key,report_value = [],[]
        for k in report_result:
           report_key.append(k)
           report_value.append(report_result[k])
        return report_key ,report_value


    @staticmethod
    def get_additional_key_and_value():
        additional_path = get_current_dir(r"Test_Data\additional.yml")
        additional_result = YamlOperator(additional_path).read()
        radditional_key, radditional_value = [], []
        for k in additional_result:
            radditional_key.append(k)
            radditional_value.append(additional_result[k])
        return radditional_key, radditional_value


    @staticmethod
    def get_index1(lst=None, item=''):
        return [index for (index, value) in enumerate(lst) if value == item]


def get_report_number():
    key, keyvalue = Report().get_report_key_and_value()
    number = Report().get_index1(keyvalue, True)
    return number


def get_report_value():
    value = []
    key, keyvalue = Report().get_report_key_and_value()
    length = len(get_report_number())
    for i in range(length):
        value.append(key[get_report_number()[i]])
    return value


def zip_file_name(number,value):
    """
    :param number: list
    :param value: list
    :return: str
    """
    length = len(number)
    for i  in range(length):
        if value[i] == 'platform':
            value[i] = Report().get_platform()
        elif value[i] =='config':
            value[i] = Report().get_config()
        elif value[i] =='uut_mac':
            value[i] = Report().get_mac_adress()[1]
        elif value[i] =='test_set_id':
            value[i] = Report().get_set_ID()
        elif value[i] =='testsetpath':
            value[i] = Report().get_testsetpath()
        elif value[i] == 'Timestamp':
            value[i] = Report().get_start_time()
    if length == 2:
        zip_file_name = str('{0}_{1}'.format(value[0] ,value[1]))
    elif length ==3:
        zip_file_name = str('{0}_{1}_{2}'.format(value[0],value[1],value[2]))
    elif length ==4:
        zip_file_name =  str('{0}_{1}_{2}_{3}'.format(value[0],value[1],value[2],value[3]))
    elif length ==5:
        zip_file_name = str('{0}_{1}_{2}_{3}_{4}'.format(value[0], value[1], value[2], value[3],value[4]))
    elif length ==6:
        zip_file_name = str('{0}_{1}_{2}_{3}_{4}_{5}'.format(value[0], value[1], value[2], value[3], value[4], value[5]))

    return zip_file_name


# def get_zip_name():
#     """get zip file name"""
#     report = Report()
#
#     zip_file_name = str('{uut_config}_{mac}_{testid}_{testsetpath}_{Timestamp}'.format(uut_config = report.get_config(),
#                                                                         mac = report.get_mac_adress()[1],
#                                                                        testid = report.get_set_ID(),
#                                                                         testsetpath = report.get_testsetpath(),
#                                                                        Timestamp = report.get_start_time()))
#
#     return zip_file_name


