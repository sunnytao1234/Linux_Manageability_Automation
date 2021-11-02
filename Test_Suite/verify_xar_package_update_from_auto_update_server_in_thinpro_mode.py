# -*- coding: utf-8 -*-
# @time         :   9/8/2021
# @author       :   arthur.zhang
# @case name    :   Verify XAR Package update from auto-update server in Thinpro mode
import logging
import pyautogui
import requests
from Test_Script.ts_common.common import CaseFlowControl, switch_thinpro_mode, PLATFORM
from Common.exception import CaseRunningError, RestoreEnvironmentError
from Common.common_function import reboot_command, GLOBAL_CONFIG_FROM_UUT, VERSION
from Test_Script.ts_common.pic_objects import AutoUpdate, Network, SystemInformation
from Test_Script.ts_common.common import Registry, wait, run_command
from config import INT_1, INT_34, BASE_DIR, GlobalConfig, INT_5
from Common.log import log

"""
Contact Person: Javen,Chen
Tips:
    * Use Citrix Pack Update instead of choosing from three types of packs
"""


class VerifyXarPackageAutoUpdateTpMode(CaseFlowControl):
    dns_servers = "15.83.248.216"
    dns_domains = "tcqaauto.sh"
    post_url = GlobalConfig.http_dependency.url_data_action.value
    json_data_for_update = {
        "method": "copy",
        "from_path": f"\\\\15.83.248.223\\ftp\\Thinpro_{VERSION}\\Manageability\\Manual\\Verify_XAR_Package_Update",
        "to_path": f"\\\\15.83.248.217\\auto-update\\{PLATFORM}",
    }

    def __init__(self, script_name, case_name, exception=(CaseRunningError,)):
        super().__init__(script_name=script_name, case_name=case_name, exception=exception)
        self.auto_update = AutoUpdate.create_object()
        self.network = Network.create_object()
        self.system_info = SystemInformation.create_object()

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

    def check_citrix_has_installed(self):
        """
        Index: 0
        """

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

    def check_citrix_pack_update_success(self):
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
        ]


def start(case_name, **kwargs):
    v = VerifyXarPackageAutoUpdateTpMode(script_name=VerifyXarPackageAutoUpdateTpMode.__name__,
                                         case_name=case_name)
    v.start()
