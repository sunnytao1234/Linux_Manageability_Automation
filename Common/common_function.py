import datetime
import os
import time
import re
import subprocess
import socket
import copy
import yaml
import pyautogui
from Common import file_transfer
from config import *
import traceback
import cv2
import shutil
import pymouse
import pykeyboard
from Common.file_transfer import FTPUtils
from Common.file_operator import YamlOperator
from Common.log import log
from Common.exception import CaseRunningError, MemoryNotSufficient

pyautogui.FAILSAFE = False
mouse = pymouse.PyMouse()
kb = pykeyboard.PyKeyboard()


def get_current_dir(*args):
    """
    :param args: use like os.path.join(path, *path)
    :return: absolute path
    """
    if args:
        path = os.path.join(str(BASE_DIR.absolute()), *args)
    else:
        path = str(BASE_DIR.absolute())
    if OSType == OS_Windows:
        return "\\".join(path.split("/"))
    return "/".join(path.split("\\"))


def collect_report():
    """
    collect report and send to ALM server for automated return result to ALM
    alm need addition.yml(case<->alm information), ip.yml(cases result)
    :return:
    #By: balance
    """
    # expect only ip.yml exist in test_report
    global_conf = YamlOperator(get_current_dir('Test_Data', 'global_config.yaml')).read()
    ftp_svr = global_conf['alm_ftp']['server']
    ftp_user = global_conf['alm_ftp']['username']
    ftp_pass = global_conf['alm_ftp']['password']
    ftp_path = global_conf['alm_ftp']['report_path']
    result_file = get_folder_items(get_current_dir('Test_Report'), file_only=True, filter_name='.yaml')[0]
    log.info(f'[common][collect result]Get result file: {result_file}')
    prefix = time.strftime("test_%m%d%H%M%S", time.localtime())
    log.info('[common][collect result]Copy additional.yml and ip.yml to test report')
    shutil.copy(get_current_dir('Test_Data', 'additional.yml'),
                get_current_dir('Test_Report', '{}_add.yml'.format(prefix)))
    shutil.copy(get_current_dir('Test_Report', result_file),
                get_current_dir('Test_Report', '{}_result.yml'.format(prefix)))
    try:
        ftp = file_transfer.FTPUtils(ftp_svr, ftp_user, ftp_pass)
        ftp.change_dir(ftp_path)
        ftp.upload_file(get_current_dir('Test_Report', '{}_result.yml'.format(prefix)), '{}_result.yml'.format(prefix))
        ftp.upload_file(get_current_dir('Test_Report', '{}_add.yml'.format(prefix)), '{}_add.yml'.format(prefix))
        ftp.close()
        log.info('[common][collect result]upload report to ftp server')
    except:
        log.error('[common][collect result]FTP Fail Exception:\n{}'.format(traceback.format_exc()))


# Function author: Nick
def now():
    now_time = datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
    return now_time


# Function author: Nick
def get_ip():
    if OSType == 'Linux':
        wired_status = subprocess.getoutput("mclient --quiet get tmp/NetMgr/eth0/IPv4/status")
        if wired_status == "1":
            sys_eth0_ip = subprocess.getoutput("ifconfig | grep eth0 -A 1 | grep -i 'inet'")
            result = re.search(r"(?i)(?:inet|inet addr)[: ]([\\.\d]+)", sys_eth0_ip)
            try:
                assert result, "Get eth0 ip fail"
                eth0_ip = result.group(1)
                return eth0_ip
            except AssertionError as e:
                pass

        wireless_status = subprocess.getoutput("mclient --quiet get tmp/NetMgr/wlan0/IPv4/status")
        if wireless_status == "1":
            sys_wlan0_ip = subprocess.getoutput("ifconfig | grep wlan0 -A 1 | grep -i 'inet'")
            result = re.search(r"(?i)(?:inet|inet addr)[: ]([\\.\d]+)", sys_wlan0_ip)
            try:
                assert result, "Get eth0 ip fail"
                wlan0_ip = result.group(1)
                return wlan0_ip
            except AssertionError as e:
                pass

        sys_eth1_ip = subprocess.getoutput("ifconfig | grep eth1 -A 1 | grep -i 'inet'")
        result = re.search(r"(?i)(?:inet|inet addr)[: ]([\\.\d]+)", sys_eth1_ip)
        if result:
            return result.group(1)
        else:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
    else:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return ip


# Function author: justin
def check_ip_yaml():
    ip_yaml_path = get_current_dir('Test_Data', 'ip.yml')
    if os.path.exists(ip_yaml_path):
        with open(ip_yaml_path, encoding='utf-8') as f:
            ip = yaml.safe_load(f)
            if ip:
                return ip[0]
            else:
                return '127.0.0.1'
    else:
        f = open(ip_yaml_path, 'w')
        f.close()
        with open(ip_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump([get_ip()], f, default_flow_style=False)
        return get_ip()


def load_global_parameters():
    # path = r'{}/Test_Data/additional.yml'.format(get_current_dir())
    path = os.path.join(get_current_dir(), 'Test_Data', 'additional.yml')
    data_dic = yaml.safe_load(open(path))
    return data_dic


def os_configuration():
    if OSType == 'Linux':
        os_config = subprocess.getoutput('mclient --quiet get tmp/SystemInfo/general/ProductConfig')
        if os_config.strip() == 'zero':
            return 'smart_zero'
        elif os_config.strip() == 'standard':
            return 'thinpro'
    else:
        pass


def new_cases_result(file, case_name, result="Fail"):
    result = [{'case_name': case_name,
               'uut_name': check_ip_yaml(),
               'result': result,
               'steps': []
               }]
    if not os.path.exists(file):
        f = open(file, 'w')
        f.close()
    with open(file, 'r') as f:
        current_report = yaml.safe_load(f)
    if isinstance(current_report, list):
        for report in current_report:
            if report['case_name'] == case_name:
                return
        current_report.extend(result)
    else:
        current_report = result

    with open(file, 'w') as f:
        yaml.safe_dump(current_report, f)


def update_cases_result(file, case_name, step):
    with open(file, 'r') as f:
        current_report = yaml.safe_load(f)
    for report in current_report:
        if report['case_name'] == case_name:
            report['steps'].append(step)
            case_status = True
            for sub_step in report['steps']:
                if sub_step['result'].upper() == 'FAIL':
                    case_status = False
                    break
            if case_status:
                report['result'] = 'Pass'
            else:
                report['result'] = 'Fail'
            break

    with open(file, 'w') as f:
        yaml.safe_dump(current_report, f)


def add_windows_user(username, password, group='users'):
    # Default group is Users
    os.system('net user /delete {}'.format(username))
    os.system('net user /add {} {}'.format(username, password))
    if group == 'Administrators':
        os.system('net localgroup Administrators {} /add'.format(username))
        return True
    else:
        return True


def get_folder_items(path, **kwargs):
    """
    get folder items without recursion
    :param path: str, path like './Test_Report' or '/root/PycharmProjects/linux_automation_script2/Common'
    :return:
    """
    safe_mode = kwargs.get("safe_mode", True)
    filter_name = kwargs.get("filter_name", "")
    file_only = kwargs.get("file_only", False)
    file_path = "/".join(os.path.realpath(path).split("\\"))
    if not os.path.exists(file_path) and safe_mode:
        os.makedirs(file_path)
    file_list = os.listdir(file_path)
    if filter_name:
        filter_name_list = []
        for i in file_list:
            if filter_name.upper() in i.upper():
                filter_name_list.append(i)
        file_list = filter_name_list
    if file_only:
        for i in copy.deepcopy(file_list):
            dir_path = file_path + "/{}".format(i)
            if os.path.isdir(dir_path):
                file_list.remove(i)
    return file_list


def get_folder_items_recursion(path, **kwargs):
    file_list = get_folder_items(path, **kwargs)
    all_file = []
    for i in file_list:
        new_path = os.path.join(path, i)
        if "__pycache__" in new_path:
            continue
        elif os.path.isdir(new_path):
            all_file = all_file + get_folder_items_recursion(new_path, **kwargs)
        else:
            all_file.append(i)
    return all_file


# Function author: justin
def add_to_startup_script(i):
    with open('/writable/root/auto_start_setup.sh', 'a') as s:
        res = get_folder_items(get_current_dir(), file_only=True)
        if i in res:
            s.write("{}\n".format(get_current_dir() + '/' + i))
        elif '/' in i:
            s.write("{}\n".format(i))
    time.sleep(0.2)
    os.system("chmod 777 /writable/root/auto_start_setup.sh")
    time.sleep(0.2)

# arthur


def add_linux_script_startup(trigger_script, stop_flag_path):
    """
    create an auto startup shell and save as 'auto_start_setup.sh'
    :param trigger_script: exec file path, the script will be run after linux power on, reboot and logoff
    :param stop_flag_path: str, a path, exit shell listening if the file exists and status is 'finished'
    :return:
    """
    log.info("Start add auto startup")
    src = BASE_DIR / 'auto_start_setup.sh'
    # Auto Startup Service Path
    path_auto_service = BASE_PATH_TEST_DATA / 'td_dependency' / "auto.service"
    refactor_auto_service = BASE_PATH_TEST_REPORT / "auto.service"
    src_auto = str(refactor_auto_service.absolute())
    dst_auto = "/etc/systemd/system/auto.service"
    dst_wants = "/etc/systemd/system/multi-user.target.wants/auto.service"
    save_path = BASE_DIR / 'auto_start_setup.sh'
    path_auto_sh = BASE_PATH_TEST_DATA / 'td_dependency' / 'auto.sh'

    with open(str(path_auto_sh.absolute()), "r") as f1,\
         open(str(save_path.absolute()), 'w') as f2:
        first_line = f1.readline()
        f2.write(first_line)
        f2.write(f"exec_file={trigger_script}\n")
        f2.write(f"flag_file={stop_flag_path}\n")
        left_lines = f1.read()
        f2.write(left_lines)

    time.sleep(INT_1)
    os.system(f"chmod 777 {str(save_path.absolute())}")

    # change and copy service to uut user.target.wants
    log.info(f"Create Service{str(refactor_auto_service.absolute())}")
    with open(str(path_auto_service.absolute()), "r") as f1, \
         open(str(refactor_auto_service.absolute()), 'w') as f2:
        for _ in range(4):
            line = f1.readline()
            f2.write(line)
        f2.write(f"ExecStart = {str(src.absolute())}\n")
        lines = f1.read()
        f2.write(lines)
    time.sleep(INT_1)

    if os.path.exists(dst_wants):
        os.remove(dst_wants)
    if os.path.exists(dst_auto):
        os.remove(dst_auto)
    shutil.copyfile(src_auto, dst_auto)
    time.sleep(1)
    os.system("ln -s {} {}".format(dst_auto, dst_wants))
    return


# Function author: justin
def linux_rm_startup_script(name=''):
    os.system("fsunlock")
    time.sleep(0.2)
    if name:
        if type(name) == list:
            for s in name:
                batch_rm_startup_script(s)
        else:
            batch_rm_startup_script(name)
    else:
        os.system("rm /etc/init/auto-run-automation-script.conf")
        os.system("rm /writable/root/auto_start_setup.sh")
    time.sleep(0.1)


# Function author: justin
def batch_rm_startup_script(name):
    if '/' in name:
        with open('/root/auto_start_setup.sh', 'r') as f:
            lis = f.readlines()
            print(lis)
            for i in lis:
                if i.strip('\n').split('/') == name.split('/'):
                    print(i.strip('\n').split('/'), name.split('/'))
                    lis.remove(i)
        with open('/root/auto_start_setup.sh', 'w') as f:
            print(lis)
            for i in lis:
                f.write(i)
    else:
        os.system('sed -i "/{}/d" /root/auto_start_setup.sh'.format(name))


def open_window(name):
    log.info("start move mouse")
    pyautogui.moveTo(100, 1)
    time.sleep(1)
    log.info("start send ctrl alt s")
    pyautogui.hotkey('ctrl', 'alt', 's')
    time.sleep(5)
    log.info("start type {}".format(name))
    pyautogui.typewrite(name, interval=0.3)
    time.sleep(2)
    pyautogui.press('enter')
    time.sleep(5)
    log.info("end")


def close_window():
    time.sleep(3)
    pyautogui.hotkey('ctrl', 'alt', 'f4')


def close_window_with_check(picture):
    time.sleep(3)
    pyautogui.hotkey('ctrl', 'alt', 'f4')
    if check_window("T", picture):
        return True
    else:
        return False


def check_window(runflag, picture):
    count = 0
    time.sleep(3)
    if runflag == "F":
        while count <= 5:
            system_window = pyautogui.locateOnScreen(picture)
            print(system_window)
            if system_window is not None:
                log.info("window opens successfully")
                return True
            else:
                log.info("window opens failed!")
                count += 1
                time.sleep(1)
                if count == 6:
                    return False
    else:
        while count <= 5:
            system_window = pyautogui.locateOnScreen(picture)
            print(system_window)
            if system_window is None:
                log.info("window closes successfully")
                return True
            else:
                log.info("window closes failed!")
                count += 1
                if count == 6:
                    return False


def delete_folder(top):
    import os
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))


def show_desktop():
    time.sleep(20)
    pyautogui.hotkey('ctrl', 'alt', 'end')


def logoff():
    show_desktop()
    time.sleep(1)
    pyautogui.rightClick()
    time.sleep(1)
    pyautogui.hotkey("up")
    time.sleep(1)
    pyautogui.hotkey("enter")
    time.sleep(1)
    pyautogui.hotkey("enter")
    time.sleep(1)
    pyautogui.hotkey("enter")


def reboot():
    show_desktop()
    time.sleep(1)
    pyautogui.rightClick()
    time.sleep(1)
    pyautogui.hotkey("up")
    time.sleep(1)
    pyautogui.hotkey("enter")
    time.sleep(1)
    pyautogui.hotkey("down")
    time.sleep(1)
    pyautogui.hotkey("down")
    time.sleep(1)
    pyautogui.hotkey("enter")
    time.sleep(1)
    pyautogui.hotkey("enter")


def get_position(img, region=None, similaity=0.97,
                 base_dir=os.path.join(get_current_dir(), 'Test_Data', 'td_power_manager', 'AD')):
    # img=os.path.join(os.getcwd(),"Test_Data","import_cert_and_lunch_firefox",img)
    if base_dir:
        img = os.path.join(base_dir, img)
    # print(img)
    count = 5
    count1 = count
    while count:
        part_img = cv2.imread(img, 0)
        w, h = part_img.shape[::-1]
        if region is None:
            pyautogui.screenshot().save("temp.png")
            full_img = cv2.imread("temp.png", 0)
            res = cv2.matchTemplate(part_img, full_img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if max_val > similaity:
                # print("find :" + img + " with similaity " + str(max_val) + " in full screen")
                log.info("find :" + img + " with similaity " + str(max_val) + " in full screen")
                return (max_loc[0], max_loc[1], w, h), (int(max_loc[0] + w / 2), int(max_loc[1] + h / 2))
            else:
                # print("Not find :" + img + " with similaity " + str(max_val) + "in region:" + str(region))
                log.info("Not find :" + img + " with similaity " + str(max_val) + "in region:" + str(region))
        else:
            pyautogui.screenshot(region=region).save("temp.png")
            full_img = cv2.imread("temp.png", 0)
            res = cv2.matchTemplate(part_img, full_img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if max_val > similaity:
                # print("find :"+img+" with similaity "+str(max_val)+"in region:"+str(region))
                log.info("find :" + img + " with similaity " + str(max_val) + "in region:" + str(region))
                return (max_loc[0], max_loc[1], w, h), (int(max_loc[0] + w / 2), int(max_loc[1] + h / 2))
            else:
                # print("Not find :" + img + " with similaity " + str(max_val) + "in region:" + str(region))
                log.info("Not find :" + img + " with similaity " + str(max_val) + "in region:" + str(region))

        count = count - 1
        # print("can not find :" + img + " :wait 1s repeat")
        log.info("can not find :" + img + " :wait 1s repeat")
    # print("can not find " + img + " in "+str(count1)+" repeats")
    log.info("can not find " + img + " in " + str(count1) + " repeats")
    return False


def screen_resolution():
    return pyautogui.size()


def case_steps_run_control(steps_list, name, *args, **kwargs):
    case_steps_file = os.path.join(get_current_dir(), "{}_case_steps.yml".format(name))
    if not os.path.exists(case_steps_file):
        list_dict = {}
        for s in steps_list:
            list_dict[s] = "norun"
        steps_yml = YamlOperator(case_steps_file)
        steps_yml.write(list_dict)

    steps_yml = YamlOperator(case_steps_file)
    for step in steps_list:
        steps_dict = steps_yml.read()
        for key, value in steps_dict.items():
            if step == key and value.lower() != "finished":
                steps_dict[key] = "finished"
                steps_yml.write(steps_dict)
                result = getattr(sys.modules[name], step)(*args, **kwargs)
                # result = eval(key)
                if result is False:
                    os.remove(case_steps_file)
                    return False
        if steps_list.index(step) == len(steps_list) - 1:
            os.remove(case_steps_file)
            return True


def load_data_from_ftp():
    file_obj = YamlOperator(get_current_dir('Test_Data', 'global_config.yaml'))
    content = file_obj.read()
    ftp_server = content['td_ftp']['server']
    ftp_user = content['td_ftp']['username']
    ftp_passwd = content['td_ftp']['password']
    td_path = content['td_ftp']['td_path']
    try:
        ftp = FTPUtils(ftp_server, ftp_user, ftp_passwd)
        ftp.change_dir(td_path)
        folders = ftp.get_item_list('')
        for folder in folders:
            if not ftp.is_item_file(folder):
                ftp.download_dir(folder, get_current_dir(folder))
        ftp.close()
    except:
        log.error('ftp exception:\n{}'.format(traceback.format_exc()))


def prepare_for_framework():
    file_path = get_current_dir('Test_Data', 'additional.yml')
    file_obj = YamlOperator(file_path)
    content = file_obj.read()
    site = content.get('AutoDash_Site')
    if site:
        return
    else:
        user_defined_data = get_current_dir('Test_Data', 'User_Defined_Data')
        if os.path.exists(user_defined_data):
            log.info('removing {}'.format(user_defined_data))
            shutil.rmtree(user_defined_data)
            time.sleep(3)
        for k, v in content.items():
            if 'User_Defined_Data'.upper() in str(k).upper():
                log.info('will download user data')
                break
        else:
            log.info('no uer defined data to be download')
            return
        file = get_current_dir('Test_Data', 'ftp_config.yaml')
        fo = YamlOperator(file)
        ftp_para = fo.read()
        for k, v in content.items():
            if 'User_Defined_Data'.upper() in str(k).upper():
                source = str(v)
                linux_path = source.replace('\\', '/')
                host = linux_path.split('/')[2]
                for each in ftp_para:
                    ip = each.get('ip')
                    user = each.get('user')
                    password = each.get('password')
                    if ip == host:
                        break
                else:
                    log.info('ftp_config.yaml has no parameters for {}'.format(host))
                    continue
                log.info('download user data from {} to UUT'.format(host))
                last_level_folder = os.path.split(linux_path)[1]
                folder_path = '/'.join(linux_path.split('/')[3:])
                if last_level_folder.upper() in ['USER_DEFINED_DATA']:
                    dst = get_current_dir('Test_Data', last_level_folder)
                else:
                    dst = get_current_dir('Test_Data', 'User_Defined_Data', last_level_folder)
                n = 0
                while True:
                    try:
                        log.info('download {} to {}'.format(source, dst))
                        ftp = FTPUtils(host, user, password)
                        ftp.download_dir(folder_path, dst)
                        break
                    except:
                        if n > 30:
                            log.info(traceback.format_exc())
                            break
                        else:
                            n += 5
                            time.sleep(5)


def get_report_base_name():
    additional_path = get_current_dir('Test_Data', 'additional.yml')
    if os.path.exists(additional_path):
        file_obj = YamlOperator(additional_path)
        content = file_obj.read()
        site = content.get('AutoDash_Site')
    else:
        site = None
    if site:
        base_name = '{}.yaml'.format(site)
    else:
        base_name = '{}.yaml'.format(check_ip_yaml())
    return base_name


def check_free_memory(status="before"):
    os.system(f"echo {status}: >> free.txt")
    os.system("free >> free.txt")


def log_cache(dtype="-k", relative_path="free.txt"):
    """
    command: free
    relative_path: path start from the project
     -b, --bytes         show output in bytes
         --kilo          show output in kilobytes
         --mega          show output in megabytes
         --giga          show output in gigabytes
         --tera          show output in terabytes
         --peta          show output in petabytes
    -k, --kibi          show output in kibibytes
    -m, --mebi          show output in mebibytes
    -g, --gibi          show output in gibibytes
         --tebi          show output in tebibytes
         --pebi          show output in pebibytes
    -h, --human         show human-readable output
         --si            use powers of 1000 not 1024

    """
    path = get_current_dir(relative_path)
    os.system(f"free {dtype} >> {path}")
    return path


def cache_collection(level: int = 1):
    """
    params: level, int,
        0: not release cache
        1: release page cache
        2: release both dentries and inodes cache
        3: release both 1 and 2
    """
    os.system(f"echo {level} > /proc/sys/vm/drop_caches")


def get_global_config(*keys):
    """
    :params: keys, tuple
    if key not exist, raise ValueError
    """
    file_dict = {}
    path = get_current_dir('Test_Data/global_config.yaml')
    if os.path.exists(path):
        file_obj = YamlOperator(path)
        file_dict = file_obj.read()
    else:
        log.warning("Not Exist {}".format(path))
    if not keys:
        return file_dict
    new_value = copy.deepcopy(file_dict)
    for i in keys:
        value = new_value.get(i, None) if isinstance(new_value, dict) else None
        if not value:
            index = keys.index(i)
            raise ValueError("Key not Exist, origin: {}".format(" -> ".join(keys[:index + 1])))
        new_value = value
    return new_value


def check_water_mark():
    path = "/usr/lib/hptc-watermark"
    if os.path.exists(path):
        os.system("rm -r {}".format(path))
        os.system("reboot")
        time.sleep(10)


def reboot_command():
    os.system("reboot")
    time.sleep(30)


def change_reboot_status(status=1):
    path = get_current_dir("reboot.txt")
    with open(path, "w") as f:
        f.write(str(status))


def need_reboot() -> int:
    """
     0: not need reboot
     another: need reboot
     """
    path = get_current_dir("reboot.txt")
    if not os.path.exists(path):
        return 0
    with open(path, "r") as f:
        res = f.read().strip()
    if not res:
        return 0
    return int(res)


def get_hostname() -> str:
    """
    Get the UUT hostname
    """
    return subprocess.getoutput("mclient --quiet get root/Network/Hostname")


def gateway_exists() -> str:
    resp = subprocess.getoutput("route -n |grep '0'")
    if resp:
        return subprocess.getoutput("route -n |grep UG")
    log.warning("Can't Find Any Wire Connection")
    return "1"


def workaround_gateway_miss():
    """
    GateWay Missing sometimes cause by the file '/etc/dhcp/dhclient.conf ' is incomplete
    Replace the .conf and reboot can handle the problem
    """
    # DHCP Config File for case of Gateway not found
    config_path = BASE_PATH_TEST_DATA / 'td_dependency' / 'dhclient.conf'
    host_name = get_hostname().strip("\n")
    format_line = f'send host-name "{host_name}";'
    source_path = "/etc/dhcp/dhclient.conf"
    with open(str(config_path.absolute()), "r") as f:
        source = f"{format_line}\n{f.read()}"
    with open(source_path, "w") as f:
        f.write(source)
    time.sleep(1)


def change_switch_user_action(default='none'):
    """
    After Thinpro 7.2 SP2, it is the default setting when people changing root to user mode will logout
    """
    subprocess.getoutput(f"mclient --quiet set root/users/root/switchToUserAction '{default}' && mclient commit")


class GlobalConfigFromUUT:
    save_path = get_current_dir('Test_Report/temp')
    save_file = get_current_dir('Test_Report/temp/temp_global_config.yaml')
    format_compare_result = "Expect: {} Actual: {}"
    has_saved = False

    @classmethod
    def save_data(cls, **data):
        """
        eg. data:
            (key1=value1, key2=value2) => {'key1': 'value1', 'key2': 'value2'}
        """
        if cls.has_saved:
            log.warning("GlobalConfigFromUUT Data has been created")
            return
        elif os.path.exists(cls.save_file):
            cls.has_saved = True
            log.warning(f"temp_global_config.yaml has been created, Path: {cls.save_file}, Start Set Attr")
            global_dict = YamlOperator(cls.save_file).read()
            for key, value in global_dict.items():
                setattr(cls, key, value)
            return
        os.makedirs(cls.save_path, exist_ok=True)
        YamlOperator(cls.save_file).write(data)
        log.info(f"Create temp_global_config.yaml, Path: {cls.save_file}")
        for key, value in data.items():
            setattr(cls, key, value)
        return

    @classmethod
    def get_data(cls, *keys, safe=False) -> list:
        """
        Read UUT Default Data from yaml
        :param keys, string list, the key you want to search
        :param safe, bool, False will raise error if the key not in yaml
        """
        if not os.path.exists(cls.save_file):
            return ["" for _ in range(len(keys))]
        global_dict = YamlOperator(cls.save_file).read()
        results = list(map(lambda key: global_dict.get(key, ""), keys))
        if safe or all(results):
            return results
        else:
            raise ValueError(f"Get Value From Registry Error: {keys}, {results}")

    @classmethod
    def check_data(cls, **data):
        """
        :data dict, {key: value(type: str)}
            key: key in temp_global_config.yaml
            value: str, expectational value
            !!! the data value must be a string
        """
        if not data:
            log.warning("No data input")
            return
        data_keys = list(data.keys())
        expected_values = list(data.values())
        actual_values = cls.get_data(*data_keys, safe=True)

        def compare(expect, actual):
            if expect == actual:
                return True
        bool_results = list(map(compare, expected_values, actual_values))

        result_list = []
        for index, expect_value in enumerate(expected_values):
            result_list.append(cls.format_compare_result.format(expect_value, actual_values[index]))
        body = "\n".join(result_list)
        if all(bool_results):
            content = f"Check Data Pass!\n{body}"
            log.info(content)
        else:
            content = f"Check Data Fail!\n{body}"
            raise CaseRunningError(content)
        return


GLOBAL_CONFIG_FROM_UUT = GlobalConfigFromUUT()


def memory_check(dtype="-m", limit: int = 300, strict_mode=True):
    """
    check memeory > limit
    raise ValueError if strict_mode is Ture else return False
    """
    try:
        res = os.popen(f"free {dtype}").readlines()
        line_name = res[0]
        line_value = res[1]
        index = line_name.index("available")
        available_str = line_value[index: index + len("available")].strip("kbgyteKBGYTE ")
        avail = float(available_str)
        print(avail)
    except Exception as e:
        log.error(e)
        return -1
    if avail < limit and strict_mode:
        raise MemoryNotSufficient("current Memory is not sufficient! Current: {}".format(avail))
    elif avail < limit:
        return False
    return True


VERSION = subprocess.getoutput('cat /etc/systeminfo|grep "PRODUCT_VERSION"').split("=")[-1][1:4]

log.info(f"Thinpro Version: {VERSION}")