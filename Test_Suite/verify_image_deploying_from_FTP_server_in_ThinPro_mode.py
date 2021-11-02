# case name: Verify_image_deploying_from_FTP_server_in_ThinPro_mode

from Test_Script.ts_common.common import CaseFlowControl, switch_thinpro_mode
from Common.exception import CaseRunningError, PicNotFoundError, RestoreEnvironmentError
from Common.common_function import reboot_command, GLOBAL_CONFIG_FROM_UUT, INT_5, INT_8, INT_21, INT_2
from Test_Script.ts_common.pic_objects import AutoUpdate, Network, SystemInformation
# from Test_Script.ts_network.network import EasyView, CertificateUtil
import time
import pyautogui
from Test_Script.ts_common.common import Registry, wait, run_command
from Common.common_function import get_current_dir
from Common.file_transfer import FTPUtils
from Common.log import log
from config import BASE_DIR, INT_34


class VerifyImageDeployingFromFTPServerInThinProMode(CaseFlowControl):
    protocol = "ftp"
    auto_server_name = "autotestftp.sh.dto"
    auto_username = ""
    auto_password = ""

    auto_restore_path = "Manageability/RestoreImage"  # Restore folder
    ftp_nightly_build = "Manageability/NightlyBuild"  # Image folder

    uut_mac = SystemInformation.get_mac()
    copy_folder_from = str(BASE_DIR.absolute())
    copy_folder_to = f"Temp_Linux_Run/HP{''.join(uut_mac.split(':'))}"

    ftp_server = "15.83.248.197"  # Update server
    ftp_username = "Administrator"
    ftp_password = "Shanghai2020"

    # ftp_server = "15.83.248.223"
    # ftp_username = r"sh\joestar.sun"
    # ftp_password = "Shanghai2010"

    def __init__(self, script_name, case_name, exception=(CaseRunningError,)):
        super().__init__(script_name=script_name, case_name=case_name, exception=exception)
        # self.fire_fox = None
        self.auto_update = AutoUpdate.create_object()
        self.network = Network.create_object()
        self.system_info = SystemInformation.create_object()

        self.ftp = FTPUtils(server=self.ftp_server, username=self.ftp_username, password=self.ftp_password)

    def close_control_panel(self):
        self.auto_update.close()
        log.info("Auto update dialog closed.")

    def reset_the_registry(self):
        Registry.auto_update_ManualUpdate = GLOBAL_CONFIG_FROM_UUT.auto_update_ManualUpdate
        Registry.auto_update_enableLockScreen = GLOBAL_CONFIG_FROM_UUT.auto_update_enableLockScreen
        Registry.auto_update_enableOnBootUp = GLOBAL_CONFIG_FROM_UUT.auto_update_enableOnBootUp
        Registry.auto_update_protocol = GLOBAL_CONFIG_FROM_UUT.auto_update_protocol
        Registry.auto_update_server = GLOBAL_CONFIG_FROM_UUT.auto_update_server
        Registry.auto_update_path = GLOBAL_CONFIG_FROM_UUT.auto_update_path
        Registry.auto_update_username = GLOBAL_CONFIG_FROM_UUT.auto_update_username
        Registry.auto_update_password = GLOBAL_CONFIG_FROM_UUT.auto_update_password
        Registry.auto_update_preserveConfig = GLOBAL_CONFIG_FROM_UUT.auto_update_preserveConfig
        Registry.commit()

    def reboot(self):
        log.info("Reboot.")
        reboot_command()

    def end_and_reboot(self):
        log.info("End and reboot.")
        self.end_flow()
        reboot_command()

    # ==========================^   method   ^=====================v   logic   v===================================
    def upload_dir_all(self):
        """
        Index:0
        """
        self.set_callback_fail(['close_control_panel',
                                'reset_the_registry',
                                'end_and_reboot'])

        self.ftp.change_dir("~")    # If run this upload-method twice, we need change the path to "/"
        self.ftp.new_dir(dir_name=self.copy_folder_to)
        self.ftp.upload_dir(local_dir=self.copy_folder_from, remote_dir=self.copy_folder_to)

    def set_automatic_update_default_settings(self):
        """
        Index:1
        """
        self.set_callback_fail(['close_control_panel',
                                'reset_the_registry',
                                'end_and_reboot'])

        switch_thinpro_mode("admin")

        self.auto_update.close()
        self.auto_update.open()

        self.auto_update.check_a_checkbox(item="Enable_Automatic_Update_on_system_startup")
        self.auto_update.uncheck_a_checkbox(item="Enable_Lock_Screen_when_Automatic_Update")
        self.auto_update.check_a_checkbox(item="Enable_manual_configuration")

        self.auto_update.apply.click()
        self.auto_update.close()

    def edit_manual_configuration(self):
        """
        Index:2
        """
        self.set_callback_fail(['close_control_panel',
                                'reset_the_registry',
                                'end_and_reboot'])

        self.auto_update.open()

        self.auto_update.Protocol.click(offset=(50, 0))
        self.auto_update.Protocol_ftp.click(offset=(20, 0))
        self.auto_update.Server.send_keys(send_string=self.auto_server_name)
        self.auto_update.Path.send_keys(send_string=self.auto_restore_path)
        self.auto_update.User_name.send_keys(send_string=self.auto_username)
        self.auto_update.Password.send_keys(send_string=self.auto_password)

        apply = self.auto_update.apply
        # maybe no settings changed, apply is gray
        try:
            apply.double_check(rate=0.95)
            apply.click()
        except PicNotFoundError as e:
            log.warning(str(e))
        self.auto_update.close()
        time.sleep(INT_5)
        self.create_list_index_file_and_suspend(index=3)
        try:
            self.upload_dir_all()
        except ConnectionResetError as ee:
            log.warning(str(ee))
            raise CaseRunningError("Upload dir second fail")
        run_command("auto-update", timeout=900)

    def check_image_update_success(self):
        """
        Index:3
        """
        # set the step
        self.force_run_next_step(flag=True)
        wait(INT_34)
        # check image update success
        image_id = self.system_info.get_image_id()
        current_version = self.system_info.get_service_pack_version()
        old_id = GLOBAL_CONFIG_FROM_UUT.image_id
        old_version = GLOBAL_CONFIG_FROM_UUT.service_pack_version
        if all([old_id == image_id, old_version == current_version]):
            raise CaseRunningError(f"Check Install Image Fail!"
                                   f" Actual: {image_id} {current_version}"
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

    def check_autoupdate_settings(self):
        """
        Index:4
        """
        self.set_callback_fail(['close_control_panel',
                                'reset_the_registry',
                                'end_and_reboot'])

        protocol = self.protocol == Registry.auto_update_protocol
        server = self.auto_server_name == Registry.auto_update_server
        path = self.auto_restore_path == Registry.auto_update_path
        preserve = GLOBAL_CONFIG_FROM_UUT.get_data('auto_update_preserveConfig')[
                       0] == Registry.auto_update_preserveConfig

        change_or_not = protocol == server == path == preserve

        if change_or_not is True:
            log.info("Check auto-update settings success, no change.")
        else:
            log.error("Check auto-update settings fail, some settings changed.")
            raise CaseRunningError

    def restore_environment(self):
        """
        Index:5
        """
        self.set_callback_fail(['close_control_panel',
                                'reset_the_registry',
                                'end_and_reboot'])

        switch_thinpro_mode("admin")

        try:
            self.auto_update.Server.sendkeys(send_string=self.auto_server_name)
            self.auto_update.Path.sendkeys(send_string=self.auto_restore_path)
            self.auto_update.User_name.sendkeys(send_string=self.auto_username)
            self.auto_update.Password.sendkeys(send_string=self.auto_password)
            self.auto_update.apply.click()

            self.create_list_index_file_and_suspend(index=6)
            self.upload_dir_all()

            run_command("auto-update", timeout=900)
        except CaseRunningError as e:
            raise RestoreEnvironmentError(str(e))

    def restore_service_pack_environment(self):
        """
        Index:6
        """
        self.set_callback_success(["reset_the_registry",
                                   "end_and_reboot"])

        switch_thinpro_mode("admin")

        try:
            self.auto_update.Server.sendkeys(send_string=self.auto_server_name)
            self.auto_update.Path.sendkeys(send_string=self.ftp_nightly_build)
            self.auto_update.User_name.sendkeys(send_string=self.auto_username)
            self.auto_update.Password.sendkeys(send_string=self.auto_password)
            self.auto_update.apply.click()

            run_command("auto-update", timeout=900)

            if not self.system_info.get_service_pack_version():
                raise CaseRunningError("Nightly Build Install Fail")
        except CaseRunningError as e:
            raise RestoreEnvironmentError(str(e))

    def check_service_pack_install_success(self):
        """
        index: 7
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

    def set_method_list(self) -> list:
        return [
            "upload_dir_all",
            "set_automatic_update_default_settings",
            "edit_manual_configuration",
            "check_image_update_success",
            "check_autoupdate_settings",
            "restore_environment",
            "restore_service_pack_environment",
            "check_service_pack_install_success",
        ]

    def start(self):
        if super().start() is False:
            return False
        return True


def start(case_name, **kwargs):
    v = VerifyImageDeployingFromFTPServerInThinProMode(
        script_name=VerifyImageDeployingFromFTPServerInThinProMode.__name__,
        case_name=case_name)
    v.start()
