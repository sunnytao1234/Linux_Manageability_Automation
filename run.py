import time
import traceback
import os
import yaml
from config import GlobalConfig, BASE_DIR

from Common.common_function import add_linux_script_startup, get_current_dir, update_cases_result, load_data_from_ftp,\
    gateway_exists, workaround_gateway_miss, change_switch_user_action, new_cases_result, check_ip_yaml
from Common.log import log
from Common.file_transfer import FTPUtils
from Common import email_tool
from Common.picture_operator import capture_screen
from Common.file_operator import YamlOperator
from Common.common_function import prepare_for_framework, get_report_base_name, collect_report,\
    GLOBAL_CONFIG_FROM_UUT
from settings import *
from Common.support_design_report_style import zip_file_name, get_report_number, get_report_value
from Test_Script.ts_common.common import Registry, set_water_mark_on_background
from Test_Script.ts_common.pic_objects import SystemInformation
import pyautogui
from Common.exception import RestoreEnvironmentError

os.environ['LD_LIBRARY_PATH'] = "/usr/lib/x86_64-linux-gnu/"


def main():
    # show_desktop()
    restore_error = False
    log.info("Move mouse")
    pyautogui.moveTo(100, 100)
    pyautogui.moveTo(110, 110)
    time.sleep(1)
    os.system(f"wmctrl -r 'run' -b add,hidden")
    flag_txt = get_current_dir('flag.txt')
    path = get_current_dir('reboot.txt')
    if not os.path.exists(path):
        set_water_mark_on_background("Automation Initializing")
    if os.path.exists(get_current_dir('flag.txt')):
        with open(get_current_dir('flag.txt')) as f:
            test_flag = f.read()
            if 'TEST FINISHED' in test_flag.upper():
                return
    ip = check_ip_yaml()
    yml_path = get_current_dir("Test_Report/{}.yaml".format(ip))

    if not os.path.exists('time.txt'):
        with open('time.txt', 'w') as f:
            f.write(time.ctime())
    prepare_for_framework()
    additional_path = get_current_dir('Test_Data', 'additional.yml')
    file_obj = YamlOperator(additional_path)
    content = file_obj.read()
    site = content.get('AutoDash_Site')
    if not site:
        # check gateway exists
        if not gateway_exists():
            workaround_gateway_miss()
            os.system("reboot")
            time.sleep(30)
        # if not os.path.exists(flag_txt):
            # load_data_from_ftp()

        # add auto start up
        script_name = os.path.basename(__file__).split('.')[0]
        trigger_script = BASE_DIR / script_name
        flag_path = BASE_DIR / 'flag.txt'
        add_linux_script_startup(trigger_script=str(trigger_script.absolute()),
                                 stop_flag_path=str(flag_path.absolute()))
        # add uut default config here
        GLOBAL_CONFIG_FROM_UUT.save_data(
            installed_storage=SystemInformation.get_installed_storage(),
            total_memory=SystemInformation.get_total_memory(),
            image_id=SystemInformation.get_image_id(),
            service_pack_version=SystemInformation.get_service_pack_version(),
            uut_mac=SystemInformation.get_mac(),
            auto_update_ManualUpdate=Registry.auto_update_ManualUpdate,
            auto_update_enableLockScreen=Registry.auto_update_enableLockScreen,
            auto_update_enableOnBootUp=Registry.auto_update_enableOnBootUp,
            auto_update_protocol=Registry.auto_update_protocol,
            auto_update_server=Registry.auto_update_server,
            auto_update_path=Registry.auto_update_path,
            auto_update_username=Registry.auto_update_username,
            auto_update_password=Registry.auto_update_password,
            auto_update_preserveConfig=Registry.auto_update_preserveConfig,
                                         )
        # change user action form logout to none after tp72 sp2
        change_switch_user_action()

    if not os.path.exists(path):
        with open(path, 'w+') as f:
            f.write("0")
        time.sleep(5)
        if os.path.exists(path):
            # set manual scaling
            Registry.Automatic_Scaling = 0
            Registry.Manual_Scaling = "100"
            Registry.commit()
            time.sleep(1)
            os.popen('reboot')
            time.sleep(30)
    if not os.path.exists(get_current_dir('Test_Report')):
        os.mkdir(get_current_dir('Test_Report'))
    test_data_path = os.path.join(get_current_dir(), 'Test_Data')
    with open(get_current_dir('flag.txt'), 'w') as f:
        f.write('testing')
    if not os.path.exists(os.path.join(test_data_path, 'script.yml')):
        log.info('script.yml not exist, please check if no cases planned')
        with open(get_current_dir('flag.txt'), 'w') as f:
            f.write('test finished')
        return
    with open(os.path.join(test_data_path, 'script.yml'), 'r') as f:
        scripts = yaml.safe_load(f)
    with open(os.path.join(test_data_path, 'additional.yml'), 'r') as f:
        additional = yaml.safe_load(f)
    for script in scripts:
        script_name, script_status = list(script.items())[0]
        if script_status.upper() == 'NORUN':
            log.info('Begin to Test case {}'.format(script_name))
            set_water_mark_on_background(f"Running: {script_name.split('__')[1]}")
            try:
                case_name = script_name.split('__')[1]
                if restore_error:
                    log.warning(f"Cuz Other Case raise RestoreEnvironmentError, Skip this case {case_name}")
                    script[script_name] = 'Finished'
                    new_cases_result(yml_path, case_name, "Skip")
                    continue
                globals()[script_name.split('__')[0]].start(
                    case_name=case_name, kwargs=additional)
                script[script_name] = 'Finished'
                with open(os.path.join(test_data_path, 'script.yml'), 'w') as f:
                    yaml.safe_dump(scripts, f)
            except RestoreEnvironmentError as e:
                log.error(e.s)
                restore_error = True
                steps = {
                    'step_name': 'case exception',
                    'result': 'Fail',
                    'expect': '',  # can be string or pic path
                    'actual': '',
                    'note': traceback.format_exc()}
                base_name = get_report_base_name()
                report_file = get_current_dir('Test_Report', base_name)
                # result_file = get_current_dir(r'Test_Report', '{}.yaml'.format(check_ip_yaml()))
                update_cases_result(report_file, script_name.split('__')[1], steps)
            except:
                with open(get_current_dir('Test_Report', 'debug.log'), 'a') as f:
                    f.write(traceback.format_exc())
                capture_screen(get_current_dir('Test_Report', 'img', '{}.jpg'.format(script_name.split('__')[1]),))
                script[script_name] = 'Finished'
                with open(os.path.join(test_data_path, 'script.yml'), 'w') as f:
                    yaml.safe_dump(scripts, f)
                steps = {
                    'step_name': 'case exception',
                    'result': 'Fail',
                    'expect': '',  # can be string or pic path
                    'actual': 'img/{}.jpg'.format(script_name.split('__')[1]),
                    'note': traceback.format_exc()}
                base_name = get_report_base_name()
                report_file = get_current_dir('Test_Report', base_name)
                # result_file = get_current_dir(r'Test_Report', '{}.yaml'.format(check_ip_yaml()))
                update_cases_result(report_file, script_name.split('__')[1], steps)
        else:
            log.info('Test case {} status is Finished, Skip test'.format(script_name))

    if site:
        share_folder = content.get('share_folder')
        host = share_folder.split('/')[0]
        folder_path = '/'.join(share_folder.split('/')[1:])
        user = content.get('user')
        password = content.get('password')
        flag_path = '/{}/{}.txt'.format(folder_path, site)
        log.info('end_flag: {}'.format(flag_path))

        with open(get_current_dir('{}.txt'.format(site)), 'w') as f:
            f.write('test finished')
        ftp = FTPUtils(host, user, password)
        ftp.ftp.cwd('ThinPro_Automation_Site')
        local_folder = get_current_dir('Test_Report')
        ftp_folder = r'/{}/Test_Report'.format(folder_path)

        num = 0
        while True:
            try:
                ftp = FTPUtils(host, user, password)
                log.info('upload Test_Report folder to ftp')
                log.info(local_folder)
                log.info(ftp_folder)
                ftp.new_dir(ftp_folder)
                local_report = get_current_dir('Test_Report', '{}.yaml'.format(site))
                ftp_report = '/{}/Test_Report/{}.yaml'.format(folder_path, site)
                ftp.upload_file(local_report, ftp_report)
                ftp.upload_file(get_current_dir(r"{}.txt".format(site)), flag_path)
                break
            except:
                if num > 30:
                    traceback.print_exc()
                    break
                else:
                    num += 5
                    time.sleep(5)
    else:
        with open(get_current_dir('flag.txt'), 'w') as f:
            f.write('test finished')
        with open('time.txt') as f:
            start = f.read()
        end = time.ctime()
        report = email_tool.GenerateReport(start, end)
        report.generate()
        file = email_tool.zip_dir()
        log.info('zipped file name: {}'.format(file_obj))
        additional_email = additional.get('email') if additional.get('email') else ''
        text = email_tool.generate_text()
        set_water_mark_on_background("Sending Email")
        for _ in range(3):
            try:
                email_tool.send_mail(recipient=['ecsrdtcqaautomation@hp.com', additional_email],
                                     subject='Automation Report Linux {}'.format(
                                         zip_file_name(get_report_number(), get_report_value())),
                                     attachment=file,
                                     text=text)
                break
            except:
                log.error(traceback.format_exc())

        os.remove(file)
        os.remove('time.txt')
        try:
            collect_report()
        except Exception as e:
            print(e)
            log.error(e)
        set_water_mark_on_background(r"Automation Finished!")


if __name__ == '__main__':
    try:
        main()
    except:
        log.error(traceback.format_exc())
