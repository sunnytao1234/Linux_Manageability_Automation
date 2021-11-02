import re

from Test_Script.ts_common.common import *
from Test_Script.ts_common.pic_settings import *
from Common.log import log
from config import *


class ControlPanel(PicObjectModel, Window):
    pic_settings = CONTROL_PANEL_SETTINGS
    open_window_name = 'Control Panel'
    close_windows_name = 'Control Panel',

    def __new__(cls, *args, **kwargs):
        cls.pic_settings.update(ControlPanel.pic_settings)
        return super().__new__(cls)

    def open(self):
        super().open()
        # To Move window to top-left because some selection will be out of scope when selected
        command_resize_and_move_control_panel = f"wmctrl -r '{self.close_windows_name[-1]}' -e 0,5,40,900,670"
        run_command(command_resize_and_move_control_panel)
        wait(INT_2)

    def check_window_has_opened(self):
        """
        This method has been overwritten
        The last close_window_name is the real window name opened, you can check opened windows with command "wmctrl -l"
        The method check the <close_windows_name>[-1] with "wmctrl"
        eg. Open Network will actually open the window 'Control Panel'
            Open System Information will actually open the window 'About this Client'
        """
        if self.close_windows_name and isinstance(self.close_windows_name, tuple):
            window = self.close_windows_name[-1]
            result = check_window(window)
            if not result:
                log.warning("Start WorkAround Using Pic instead of 'CTRL+ALT+S'")
                menu = self.menu
                menu.click()
                wait(INT_5)
                pyautogui.typewrite(self.open_window_name, interval=0.3)
                wait(INT_2)
                pyautogui.press('enter')
                wait(INT_3)
                log.info("end")
            else:
                log.info(f"Check Window: {window} Exist")
        else:
            log.warning("No window name")

    def close(self):
        """
        OverWrite the Method to workaround Control Panel Can't be closed.
        When Something be change in Control Panel such as DNS settings,
        'NetWork' Window will Popup using command "wmctrl -c 'Control Panel'".
        Use the other command 'hptc-control-panel --term' to workaorund it.
        """
        super().close()
        run_command("hptc-control-panel --term")


class AutoUpdate(ControlPanel):
    pic_settings = AUTO_UPDATE_SETTINGS
    open_window_name = 'Automatic Update'
    close_windows_name = 'Control Panel',

    @property
    def apply(self):
        """
        Sometimes a small resolution will make apply button invisible.
        This is a work around.
        :return PicObjectModel, return a apply button
        """
        try:
            return self.control_apply
        except PicNotFoundError:
            log.warning("Start Resize Control Panel")
            command_resize_and_move_control_panel = f"wmctrl -r '{self.close_windows_name[-1]}' -e 0,5,40,900,670"
            run_command(command_resize_and_move_control_panel)
        return self.control_apply

    def check_a_checkbox(self, item: str):
        """
        Click the Checkbox at the front of item
        :item, key in AUTO_UPDATE_SETTINGS
        positively click the checkbox at the front of the <item> first,
        if not click successfully, check the checkbox negatively
        """
        pic_obj = getattr(self, item)
        try:
            pic_obj.checkbox_unselected.click()
        except PicNotFoundError as e:
            log.warning(str(e))
        try:
            if pic_obj.checkbox_selected:
                log.warning(f"Checkbox {item} was already checked")
        except PicNotFoundError:
            raise CaseRunningError(
                f"Error {item} on Check a checkbox, Both Checkbox Selected and Unselected were not found.")

    def uncheck_a_checkbox(self, item: str):
        """
        Click the Checkbox at the front of item
        :item, key in AUTO_UPDATE_SETTINGS
        """
        pic_obj = getattr(self, item)
        try:
            pic_obj.checkbox_selected.click()
        except PicNotFoundError as e:
            log.warning(str(e))
        try:
            if pic_obj.checkbox_unselected:
                log.warning(f"Checkbox {item} was already unchecked")
        except PicNotFoundError:
            raise CaseRunningError(
                f"Error {item} on Uncheck a checkbox, Both Checkbox Selected and Unselected were not found.")

    def check_one_default_checkbox_settings(self, item: str, expectation=True):
        """
        expectation: True, the checkbox was checked
                     False, the checkbox was unchecked
        use key 'checkbox_selected' as checkbox pic
        """
        pic_obj = getattr(self, item)
        flag = False
        try:
            if pic_obj.checkbox_selected:
                flag = True
        except PicNotFoundError as e:
            log.warning(str(e))
        if flag is expectation:
            log.info(f" Checkbox Profile as Expected."
                     f" Expect: {'Checked' if expectation else 'UnChecked'}"
                     f" Actual: {'Checked' if flag else 'UnChecked'}")
        else:
            raise CaseRunningError(f"Check Wireless Profile Error."
                                   f" Expect: {'Checked' if expectation else 'UnChecked'}"
                                   f" Actual: {'Checked' if flag else 'UnChecked'}")

    def check_default_checkbox_settings(self, **items):
        """
        check a group of items' checkbox status
        :items dict, format like { item1: True,
                                   item2: False}
        :item key in AUTO_UPDATE_SETTINGS
        """
        for each_item, expectation in items.items():
            self.check_one_default_checkbox_settings(item=each_item, expectation=expectation)


class EasyUpdate(PicObjectModel, Window):
    pic_settings = EASY_UPDATE_SETTINGS
    open_window_name = 'Easy Update'
    close_windows_name = 'Easy Tools',

    @property
    def apply(self):
        """
        Sometimes a small resolution will make apply button invisible.
        This is a work around.
        :return PicObjectModel, return a apply button
        """
        try:
            return self.control_apply
        except PicNotFoundError:
            log.warning("Start Resize Control Panel")
            command_resize_and_move_control_panel = f"wmctrl -r '{self.close_windows_name[-1]}' -e 0,5,40,900,670"
            run_command(command_resize_and_move_control_panel)
        return self.control_apply


class Network(ControlPanel):
    pic_settings = NETWORK_SETTINGS
    open_window_name = 'Network'
    close_windows_name = ('Control Panel', )

    @property
    def apply(self):
        """
        Sometimes a small resolution will make apply button invisible.
        This is a work around.
        :return PicObjectModel, return a apply button
        """
        try:
            return self.control_apply
        except PicNotFoundError:
            log.warning("Start Resize Control Panel")
            command_resize_and_move_control_panel = f"wmctrl -r '{self.close_windows_name[-1]}' -e 0,5,40,900,670"
            run_command(command_resize_and_move_control_panel)
        return self.control_apply


class SystemInformation(PicObjectModel, Window):

    pic_settings = CONTROL_PANEL_SETTINGS
    open_window_name = 'System Information'
    close_windows_name = 'About this Client',

    def check_window_has_opened(self):
        """
        This method has been overwritten
        The last close_window_name is the real window name opened, you can check opened windows with command "wmctrl -l"
        The method check the <close_windows_name>[-1] with "wmctrl"
        eg. Open Network will actually open the window 'Control Panel'
            Open System Information will actually open the window 'About this Client'
        """
        if self.close_windows_name and isinstance(self.close_windows_name, tuple):
            window = self.close_windows_name[-1]
            result = check_window(window)
            if not result:
                log.warning("Start WorkAround Using Pic instead of 'CTRL+ALT+S'")
                menu = self.menu
                menu.click()
                wait(INT_5)
                pyautogui.typewrite(self.open_window_name, interval=0.3)
                wait(INT_2)
                pyautogui.press('enter')
                wait(INT_3)
                log.info("end")
            else:
                log.info(f"Check Window: {window} Exist")
        else:
            log.warning("No window name")

    @staticmethod
    def get_installed_storage() -> float:
        """
        Get System total storage_size
        :return:
        """
        command = "lsblk|grep -i 'name' -A 1|awk '{print $4}'"
        response = run_command(command).strip()
        result = re.search(r'(?i)([\d\\.]+)G', response, re.S)
        if result:
            return float(result.group(1))
        raise CaseRunningError(f"Can't get storage by command: {command}")

    @staticmethod
    def get_image_id() -> str:
        """
        Get Image ID like 'T8X72014' with command
        :return: str
        """
        command = r'head /etc/imageid'
        return run_command(command).strip()

    @staticmethod
    def get_service_pack_version() -> str:
        """
        Get System Service Pack Version but not software
        :return: str
        """
        command = r"dpkg --list|grep hptc-sp-thinpro -A 0|awk '{print $3}'"
        result = run_command(command).strip()
        if result:
            return result
        return ""

    @staticmethod
    def get_mac():
        """
        Only test on Thinpro 7.2
        :return:
        """
        command = r"ifconfig eth0|grep ether|awk '{print $2}'"
        response = run_command(command).strip()
        if not response:
            raise ValueError(f"Can't get mac with command: {command}")
        return response

    @staticmethod
    def get_total_memory() -> str:
        """
        Only test on Thinpro 7.2
        Get Hardware Memory info
        :return:
        """
        command = r"dmidecode -t 19|grep -i 'Size'|awk '{print $3}'"
        response = run_command(command)
        if not response:
            raise ValueError(f"Can't get mac with command: {command}")
        return response

