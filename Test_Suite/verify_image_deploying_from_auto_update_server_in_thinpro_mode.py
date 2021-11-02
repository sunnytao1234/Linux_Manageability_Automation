# -*- coding: utf-8 -*-
# @time         :   9/8/2021
# @author       :   arthur.zhang
# @case name    :   Verify image deploying from auto-update server in Thinpro mode
import logging
import pyautogui
import requests
from Test_Script.ts_common.common import CaseFlowControl, switch_thinpro_mode, PLATFORM
from Common.exception import CaseRunningError, RestoreEnvironmentError
from Common.common_function import reboot_command, GLOBAL_CONFIG_FROM_UUT, VERSION
from Test_Script.ts_common.pic_objects import AutoUpdate, Network, SystemInformation
from Test_Script.ts_common.common import Registry, wait, run_command
from config import INT_1, INT_34, BASE_DIR, GlobalConfig, INT_5
from Common.file_transfer import FTPUtils
from Common.log import log

"""
Contact Person: Javen,Chen
Tips:
    * Case will not check the auto-update icon appears in task bar after reboot.
    * In Auto Update Progress, progressbar will not be checked
    * check point in system information will use command instead of UI
    * Case will fail when auto update progress end but not reboot
"""


class VerifyImageDeployFromAutoInTPMode(CaseFlowControl):
    dns_servers = "15.83.248.216"
    dns_domains = "tcqaauto.sh"
    uut_mac = SystemInformation.get_mac()
    copy_folder_from = str(BASE_DIR.absolute())
    copy_folder_to = f"Temp_Linux_Run/HP{''.join(uut_mac.split(':'))}"
    backup_ftp_server = "15.83.248.197"
    backup_ftp_server_user = "administrator"
    backup_ftp_server_password = "Shanghai2020"
    update_ftp_server = "autotestftp.sh.dto"
    ftp_image_path = f"Thinpro_{VERSION}/Manageability/Auto/RestoreImage"
    ftp_nightly_build = f"Thinpro_{VERSION}/Manageability/Manual/NightlyBuild"
    post_url = GlobalConfig.http_dependency.url_data_action.value
    json_data_for_update = {
        "method": "copy",
        "from_path": f"\\\\15.83.248.223\\ftp\\Thinpro_{VERSION}\\Manageability\\Auto\\UpdateImage",
        "to_path": f"\\\\15.83.248.217\\auto-update\\{PLATFORM}",
    }

    def __init__(self, script_name, case_name, exception=(CaseRunningError,)):
        super().__init__(script_name=script_name, case_name=case_name, exception=exception)
        self.auto_update = AutoUpdate.create_object()
        self.network = Network.create_object()
        self.system_info = SystemInformation.create_object()

    def upload_to_server(self):
        """
        wrapped method to upload all files under BaseDir to server
        """
        exception = None
        for _ in range(INT_5):
            try:
                ftp = FTPUtils(server=self.backup_ftp_server,
                               username=self.backup_ftp_server_user,
                               password=self.backup_ftp_server_password)
                ftp.new_dir(dir_name=self.copy_folder_to)
                ftp.delete_folder(remote_dir=self.copy_folder_to)
                wait(INT_1)
                ftp.change_dir("~")
                ftp.upload_dir(local_dir=self.copy_folder_from, remote_dir=self.copy_folder_to)
                break
            except Exception as e:
                log.error(str(e))
                exception = e
        else:
            raise exception

    def request(self, json_data):
        exception = None
        for _ in range(INT_5):
            try:
                pyautogui.moveRel(10, 10)
                log.info(f"Start Post: {self.post_url} Data: {json_data}")
                res = requests.post(self.post_url, json=json_data, timeout=150)
                status_code = int(res.status_code)
                response = res.text
                if 0 <= status_code - 200 < 10:
                    if response[0] == "0":
                        break
                    raise CaseRunningError(f"{response[2:]}")
                else:
                    raise CaseRunningError(f"{status_code}, {response}")

            except Exception as e:
                logging.error(str(e))
                exception = e
        else:
            raise exception

    def check_auto_update_config_is_correct(self):
        """
        Index: 0
        """
        self.set_callback_fail(["reboot"])
        switch_thinpro_mode("admin")

        self.auto_update.close()
        self.auto_update.open()
        wait(INT_5)
        self.auto_update.check_one_default_checkbox_settings(item="Enable_Automatic_Update_on_system_startup",
                                                             expectation=True)
        self.auto_update.check_one_default_checkbox_settings(item="Enable_manual_configuration",
                                                             expectation=False)
        self.auto_update.close()
        return

    def set_dns(self):
        """
        Index: 1
        """
        self.set_callback_success(["reboot"])
        self.network.open()
        wait(INT_5)
        self.network.DNS.click()
        self.network.DNS_DNS_Servers.send_keys(send_string=self.dns_servers)
        self.network.DNS_search_domains.send_keys(send_string=self.dns_domains)
        self.network.apply.click()
        wait(INT_5)
        self.network.close()

        # request server copy image to broadcast server
        self.request(json_data=self.json_data_for_update)

        # get current installed storage step has in run.py
        self.create_list_index_file_and_suspend(index=2)

        # backup file to server
        self.upload_to_server()

    def check_image_update_success(self):
        """
        Index: 2
        """
        # set the step
        wait(INT_34)
        self.force_run_next_step(flag=True)
        # check image update success
        switch_thinpro_mode("admin")

        # check image id & service pack version
        current_image_id = self.system_info.get_image_id()
        current_version = self.system_info.get_service_pack_version()
        old_id = GLOBAL_CONFIG_FROM_UUT.image_id
        old_version = GLOBAL_CONFIG_FROM_UUT.service_pack_version
        if all([old_id == current_image_id, old_version == current_version]):
            raise CaseRunningError(f"Check Install Image Fail!"
                                   f" Actual: {current_image_id} {current_version}"
                                   f" is the same as before-updating ")

        # check installed storage
        current_installed_storage = self.system_info.get_installed_storage()
        old_installed_storage = float(GLOBAL_CONFIG_FROM_UUT.installed_storage)
        if current_installed_storage - old_installed_storage > 1:
            raise CaseRunningError(f"Check Installed Storage fail!"
                                   f" Actual: {current_installed_storage}"
                                   f" Expect: {old_installed_storage}")

        # check total memory
        current_total_memory = self.system_info.get_total_memory()
        old_total_memory = GLOBAL_CONFIG_FROM_UUT.total_memory
        if current_total_memory != old_total_memory:
            raise CaseRunningError(f"Check Memory fail!"
                                   f" Actual: {current_total_memory}"
                                   f" Expect: {old_total_memory}")

    def restore_environment(self):
        """
        Index:3
        """
        self.set_callback_fail(["reset_the_registry",
                                "end_and_reboot"])
        try:
            switch_thinpro_mode("admin")
            self.network.open()
            self.network.DNS.click()
            self.network.DNS_DNS_Servers.send_keys("1")
            self.network.DNS_DNS_Servers.clear()
            self.network.DNS_search_domains.clear()
            self.network.apply.click()
            wait(INT_5)
            self.network.close()
            wait(INT_5)
            self.auto_update.open()
            wait(INT_5)
            self.auto_update.check_a_checkbox("Enable_manual_configuration")
            self.auto_update.Server.send_keys(send_string=self.update_ftp_server)
            self.auto_update.Path.send_keys(send_string=self.ftp_image_path)
            self.auto_update.apply.click()
            self.create_list_index_file_and_suspend(index=4)

            # backup file to server
            self.upload_to_server()

        except CaseRunningError as e:
            raise RestoreEnvironmentError(e.s)

        run_command("auto-update", timeout=900)
        raise CaseRunningError(f"UUT Not Reboot after run command auto-update")

    def restore_service_pack_environment(self):
        """
        Index: 4
        """
        self.set_callback_success(["reboot"])
        try:
            switch_thinpro_mode("admin")
            self.auto_update.open()
            wait(INT_5)
            self.auto_update.check_a_checkbox("Enable_manual_configuration")
            self.auto_update.Server.send_keys(send_string=self.update_ftp_server)
            self.auto_update.Path.send_keys(send_string=self.ftp_nightly_build)
            self.auto_update.apply.click()
            wait(INT_5)
            self.auto_update.close()
            self.create_list_index_file_and_suspend(index=5)
            run_command("auto-update", timeout=900)
            wait(INT_34)
        except CaseRunningError as e:
            raise RestoreEnvironmentError(e.s)

    def check_service_pack_install_success(self):
        """
        index: 5
        :return:
        """
        # check version of sp pack
        self.set_callback_success(["reset_the_registry",
                                   "end_and_reboot"])
        old_ver = GLOBAL_CONFIG_FROM_UUT.service_pack_version
        new_ver = self.system_info.get_service_pack_version()
        if not new_ver == old_ver:
            raise RestoreEnvironmentError(
                f"Nightly Build Version Error, Before: {old_ver}, "
                f"Now: {new_ver}")

    def reset_the_registry(self):
        Registry.auto_update_ManualUpdate = "0"
        Registry.commit()

    def end_and_reboot(self):
        self.end_flow()
        reboot_command()

    def reboot(self):
        reboot_command()

    def set_method_list(self) -> list:
        return [
            'check_auto_update_config_is_correct',
            'set_dns',
            'check_image_update_success',
            'restore_environment',
            'restore_service_pack_environment',
            'check_service_pack_install_success'
        ]


def start(case_name, **kwargs):
    v = VerifyImageDeployFromAutoInTPMode(script_name=VerifyImageDeployFromAutoInTPMode.__name__,
                                          case_name=case_name)
    v.start()
