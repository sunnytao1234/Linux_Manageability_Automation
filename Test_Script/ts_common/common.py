import os
from Common import picture_operator, file_operator
import pyautogui
from Common.exception import PathNotFoundError, PicNotFoundError, ClickError, TimeOutError, CaseRunningError
from Common.common_function import get_current_dir, open_window, new_cases_result, check_ip_yaml, update_cases_result,\
    get_folder_items, kb
from Common.picture_operator import capture_screen, capture_screen_by_loc, compare_pic_similarity
from Common.log import log
import time
import subprocess
from abc import abstractmethod
from Test_Script.ts_common.registry_settings import REGISTRY_SETTINGS
from config import PATH_ADDITIONAL


## get info from additonal.yml
if os.path.exists(str(PATH_ADDITIONAL.absolute())):
    AdditionalYaml = file_operator.YamlOperator(str(PATH_ADDITIONAL.absolute())).read()
    PLATFORM = AdditionalYaml["platform"]
else:
    AdditionalYaml = {}
    PLATFORM = ""


def wait(s):
    log.info(f"Wait {s} seconds")
    time.sleep(s)


def run_command(commands, timeout=15):
    log.info(f":: Start run Command: {commands}")
    result = subprocess.Popen(commands, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              shell=True)
    try:
        output, error = result.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise TimeOutError(str(e))
    return output.decode('utf-8')


def set_water_mark_on_background(message=""):
    """
    Show message on background through the type watermark
    :param message, str, if message is none, there is no watermark on background
    """
    try:
        run_command(f"hptc-set-background --root --license-watermark '{message}'", timeout=15)
    except:
        log.error(f"Set WaterMark {message} Fail")


def window_close(name):
    log.info(f'close window {name} by command')
    run_command(f"wmctrl -c '{name}'")


def check_window(name):
    time.sleep(2)
    result = run_command(f"wmctrl -l | grep -i '{name}'")
    return result


def search_file_from_usb(file_name):
    """
    :return str, absolute file path, name can be a grep in linux
    """
    folder = run_command("ls /media").strip()
    result = run_command(f"find /media/{folder} -type f -iname '{file_name}'").strip()
    if not result:
        raise CaseRunningError(f"File {file_name} not found  in /media/{folder}")
    log.info(f'Find the File: {result}')
    return result


class Window:
    open_window_name: str = ''
    close_windows_name: tuple = ()

    def open(self):
        open_window(self.open_window_name)
        self.check_window_has_opened()
        self._active_window()

    def _active_window(self):
        """
        Let window show at front of window
        """
        if self.close_windows_name:
            run_command(f"wmctrl -a '{self.close_windows_name[-1]}'")

    def close(self):
        time.sleep(2)
        for window in self.close_windows_name:
            time.sleep(2)
            window_close(window)

    def check_window_has_opened(self):
        pass

    def active_window(self):
        self._active_window()
        time.sleep(5)

    def minimize_window(self):
        run_command(f"wmctrl -r '{self.close_windows_name[-1]}' -b add,hidden")
        time.sleep(5)


class PicObjectModel:
    pic_settings = {}

    def __init__(self, loc, name, pic_path, offset=(0, 0)):
        self.name = name
        self.loc = loc
        self.pic_path = pic_path
        self.offset = offset

    def __str__(self):
        return f':: Name: {self.name} Loc: {self.loc} Path: {self.pic_path}'

    def __getattr__(self, item):
        log.info(f"-> Find Item: {item}")
        pic_path, offset, position = self.pic_settings.get(item, (None, (), ()))
        if not pic_path:
            raise KeyError(f"pic settings doesn't have Item: {item}")
        icon_path = get_current_dir(pic_path)
        if not os.path.exists(icon_path):
            raise PathNotFoundError(f"Pic Path: '{icon_path}' Not Exists, Current Path: {icon_path}")
        if not self.loc:
            element_shape = picture_operator.wait_element(icon_path, offset=(0, 0), rate=0.93)
        else:
            element_shape = self.__capture_part_screen(icon_path=icon_path, position=position)
        if not element_shape:
            raise PicNotFoundError(f"Item: '{item}' Icon not found, Current Path: {icon_path}")
        flow_obj = self.__class__(loc=element_shape, name=item, pic_path=pic_path, offset=offset)
        log.info(flow_obj)
        return flow_obj

    def __capture_part_screen(self, icon_path, position: tuple, rate=0.95) -> tuple:
        save_path = get_current_dir("loc_demo.png")
        if not position:
            return picture_operator.wait_element(icon_path, offset=(0, 0), rate=rate)
        if not len(position) == 4:
            raise KeyError("Position must be a tuple as: (left, top, width, height)")
        left, top, width, height = position
        current_x, current_y = self.loc[0]
        pos = {"left": current_x + left, "top": current_y + top, "width": width, "height": height}
        capture_screen_by_loc(file_path=save_path, loc_dic=pos)
        items = get_folder_items(icon_path, file_only=True, filter_name=".png")
        pic_path_list = list(map(lambda file_name: icon_path + f"/{file_name}", items))
        for pic_item in pic_path_list:
            element_shape = compare_pic_similarity(img=pic_item, tmp=save_path, rate=rate)
            if element_shape:
                loc, size = element_shape
                loc_x, loc_y = loc
                current_left, current_top = current_x + left + loc_x, current_y + top + loc_y
                return (current_left, current_top), size
        return ()

    @staticmethod
    def __calculate_midpoint(loc: tuple, size: tuple, offset: tuple = (0, 0)) -> tuple:
        """
        get the pic center point
        """
        loc_x, loc_y = loc
        size_x, size_y = size[1], size[0]
        offset_x, offset_y = offset
        return loc_x + int(size_x / 2) + offset_x, loc_y + int(size_y / 2) + offset_y

    def double_check(self, rate=0.95):
        """
        :param rate, int, check the pic again with more higher rate after found the element
        """
        pic_path, offset, position = self.pic_settings.get(self.name)
        icon_path = get_current_dir(pic_path)
        if position:
            size_y, size_x = self.loc[1][0: 2]
            # half_x, half_y = int(size_x / 2), int(size_y / 2)
            new_position = (- 1, - 1, size_x + 2, size_y + 2)
            element_shape = self.__capture_part_screen(icon_path=icon_path, position=new_position, rate=rate)
        else:
            element_shape = picture_operator.wait_element(icon_path, offset=(0, 0), rate=rate)

        if not element_shape:
            raise PicNotFoundError(f"Item: '{self.name}' Icon not found, Current Path: {icon_path}")
        self.loc = element_shape
        flow_obj = self.__class__(loc=element_shape, name=self.name, pic_path=pic_path)
        log.info(flow_obj)
        return flow_obj

    @classmethod
    def create_object(cls):
        name = cls.pic_settings.get("Name", cls.__name__)
        return cls(loc=(), name=name, pic_path='')

    def check_item_exists(self, item, expectation=True):
        flag = False
        try:
            item_obj = getattr(self, item)
            flag = True
        except PicNotFoundError as e:
            log.warning(str(e))
        if flag is expectation:
            log.info(f"Found Item '{item}' As Expected"
                     f" Expect: {'Exists' if expectation else 'Not Exists'}"
                     f" Actual: {'Exists' if flag else 'Not Exists'}")
        else:
            raise CaseRunningError(f"Error, Found Item '{item}' Unexpectedly"
                                   f" Expect: {'Exists' if expectation else 'Not Exists'}"
                                   f" Actual: {'Exists' if flag else 'Not Exists'}")

    def click(self, offset=(0, 0), **kwargs):
        """
        :kwargs  parameters in pyautogui.click
        """
        time.sleep(1)
        if not self.loc:
            raise ClickError(f"Can't click, Operation object not declared, Current object: {self.name}, Current Path:{self.pic_path}")
        loc = self.__calculate_midpoint(loc=self.loc[0], size=self.loc[1], offset=(self.offset[0] + offset[0],
                                                                                   self.offset[1] + offset[1]))
        log.info(f"Click Loc: X: {loc[0]}, Y: {loc[1]}")
        pyautogui.click(*loc, **kwargs)

    def double_click(self, offset=(0, 0)):
        if not self.loc:
            raise ClickError(f"Can't click, Operation object not declared, Current object: {self.name}, Current Path:{self.pic_path}")
        loc = self.__calculate_midpoint(loc=self.loc[0], size=self.loc[1], offset=(self.offset[0] + offset[0],
                                                                                   self.offset[1] + offset[1]))
        log.info(f"Click Loc: X: {loc[0]}, Y: {loc[1]}")
        pyautogui.click(*loc, clicks=2, interval=0.05)

    @staticmethod
    def clear():
        pyautogui.keyDown('backspace')
        time.sleep(4)
        pyautogui.keyUp('backspace')
        pyautogui.keyDown('delete')
        time.sleep(4)
        pyautogui.keyUp('delete')

    def send_keys(self, send_string, offset=(0, 0)):
        self.click(offset=offset)
        self.clear()
        pyautogui.typewrite(send_string, interval=0.3)

    def move_to(self, offset=(0, 0)):
        loc = self.__calculate_midpoint(loc=self.loc[0], size=self.loc[1], offset=(self.offset[0] + offset[0],
                                                                                   self.offset[1] + offset[1]))
        pyautogui.moveTo(*loc)
        time.sleep(1)


class ResultControl:

    case_name = None
    yml_path = None

    def __init__(self, case_name):
        ip = check_ip_yaml()
        self.yml_path = get_current_dir("Test_Report/{}.yaml".format(ip))
        self.case_name = case_name

    def update_class_property(self):
        """
        abstract method
        :return:
        """
        pass

    def __update_result(self):
        """
        abstract method
        :return:
        """
        pass

    def start(self):
        """
        abstract method
        :return:
        """
        pass


class ResultHandler(ResultControl):
    flag = None
    event_method_name = None
    error_msg = None
    success_msg = None
    capture = True

    def __init__(self, case_name):
        super().__init__(case_name)
        new_cases_result(self.yml_path, self.case_name)

    def update_class_property(self, **kwargs):
        self.flag = kwargs.get("return", False)
        self.event_method_name = kwargs.get("event_method").__name__
        self.error_msg = kwargs.get("error_msg", {})
        self.success_msg = kwargs.get("success_msg", {})
        self.capture = kwargs.get("capture", True)

    def __update_result(self):
        step = {'step_name': '',
                'result': 'PASS',
                'expect': '',
                'actual': '',
                'note': ''}
        step.update({'step_name': self.event_method_name})
        if not self.flag:
            if self.capture:
                path = get_current_dir("Test_Report/img/{}__{}_exception.png".format(self.case_name.replace(" ", "_"), self.event_method_name))
                log.warning(f"capture path: {path}")
                capture_screen(path)
            step.update({'result': 'Fail',
                         'expect': self.error_msg.get("expect", ""),
                         'actual': self.error_msg.get("actual", ""),
                         'note': '{}__{}_exception.png'.format(self.case_name, self.event_method_name) if self.capture else ""})
        else:

            step.update(self.success_msg)
        update_cases_result(self.yml_path, self.case_name, step)
        return

    def start(self):
        return self.__update_result()


class CaseFlowControl:
    """
    Extend the Class and rewrite method: set_method_list
    the case extended the class will create a step file at ./Test_Report/temp/<case_name>.yaml
    if <case_name>.yaml not exists, case will start from beginning
    if -1 in <case_name>.yaml shows that the case has ended
    :exception Set an expected Exception(Default) will be catch while running
    for example:
    use create_list_index_file(1): write 1(index) into file,
    then read_a_file(): return 1
    it will exec from the method_name_list[1:]
    :return: False, if no steps run or any exception happens
             True, if no error happens
    """
    default_save_path: str = get_current_dir("Test_Report/temp/{}.yaml")

    def __init__(self, script_name, case_name, exception: tuple):
        self.__dic = dict(self.__class__.__dict__)
        self.__class_name = self.__class__.__name__
        self.end_function_name = self.end_flow.__name__
        self.__dic.update({self.end_function_name:
                               CaseFlowControl.__dict__.get(self.end_function_name)})
        self.__method_name_list = []
        self.__exec = True
        self.default_save_path = self.default_save_path.format(script_name)
        self.current_step: int = -1
        self.__skip_list = []
        self.__work_around_list_fail = []
        self.__work_around_list_success = []
        self.result_handler = ResultHandler(case_name=case_name)
        self.exception = exception
        self.__force_run_next_step = False

    def force_run_next_step(self, flag: bool = False):
        """
        when case error happens, case will continue run
        :return:
        """
        self.__force_run_next_step = flag

    def update_dic(self, dic: dict):
        """
        the method will update self.__class__.__dict__
        for example:
        update_dict(CaseFlowControl.__dict__) will get a dic that has both CaseFlowControl method
        and SubClass method, if method name is the same, Subclass will instead of Parent method
        :param dic:
        :return:
        """
        dic = dict(dic)
        dic.update(self.__dic)
        self.__dic = dic

    def end_flow(self, save_path=""):
        """
        create a -1 file and stop the flow
        """
        self.create_list_index_file_and_suspend(index=-1, save_path=save_path)
        log.info("Flow {} Ended".format(self.__class_name))

    def suspend_exec(self):
        """
        stop the flow
        :return:
        """
        self.__exec = False

    def skip(self, name_list: list):
        self.__skip_list = name_list

    def set_callback_fail(self, around_list: list):
        self.__work_around_list_fail = around_list

    def extend_callback_fail(self, around_list: list):
        """
        extend the __work_around_list when work around has started
        """
        self.__work_around_list_fail.extend(around_list)

    def extend_callback_success(self, around_list: list):
        self.__work_around_list_success.extend(around_list)

    def set_callback_success(self, around_list: list):
        self.__work_around_list_success = around_list

    def exec_callback(self, around_list: list):
        while around_list:
            around_name = around_list[0]
            around_list.remove(around_name)
            around_method = self.__dic.get(around_name)
            assert around_method, "{} Not Exist".format(around_name)
            log.info("Start Callback: {}".format(around_name))
            around_method(self)
        self.__work_around_list_success = []
        self.__work_around_list_fail = []

    def __set(self):
        self.__method_name_list = self.set_method_list()
        self.__method_name_list.append("{}".format(self.end_function_name))

    @abstractmethod
    def set_method_list(self) -> list:
        """
        :return: ["a name list contains which method you want to exec", ]
        """
        pass

    def create_list_index_file_and_suspend(self, index: int = 0, save_path="", suspend=True):
        """
        the start method will stop if create the file
        :param suspend: bool, stop the flow immediately, next method will not exec
        :param index: the order in method_name_list
        :param save_path: abs_path
        :return: None
        """
        if not save_path:
            save_path = self.default_save_path
        path = os.path.dirname(save_path)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            log.warning("Create path {}".format(path))
        self.default_save_path = save_path
        file_operator.YamlOperator(save_path).write(str(index))
        if suspend and index != -1:
            log.warning(
                "Create {} Index: {}, Flow {} wil be stop immediately!".format(save_path, index, self.__class_name))
            self.suspend_exec()
        return

    def read_a_file(self, path=""):
        """
        :param path:
        :return: Index of the method_name_list,
        """
        if not path:
            path = self.default_save_path
        if not os.path.exists(path):
            return 0
        res = file_operator.YamlOperator(path).read()
        # os.remove(p)
        try:
            return int(res)
        except:
            return -1

    def start(self):
        self.__set()
        assert self.__method_name_list, "Need a method list!"
        index = self.read_a_file()
        log.info("Get Status: {}".format(index))
        if index == -1:
            log.info(" This {} Flow has Ended".format(self.__class_name))
            return
        flag = True
        self.current_step = index
        new_list = self.__method_name_list[index:]
        for method_name in new_list:

            if method_name in self.__skip_list:
                self.current_step += 1
                continue
            method = self.__dic.get(method_name)
            assert method, "{} Not Exist".format(method_name)
            log.info(">> Start Step Method {}".format(method_name))
            try:
                result_dict = {"event_method": method,
                               "return": True}
                method(self)
                self.result_handler.update_class_property(**result_dict)
                self.result_handler.start()
                self.exec_callback(self.__work_around_list_success)
            except self.exception as e:
                if self.__force_run_next_step:
                    self.__force_run_next_step = False
                else:
                    flag = False
                    self.suspend_exec()
                    self.end_flow()
                log.error(e)
                result_dict = {"event_method": method,
                               "error_msg": {"actual": "Fail at Index {} : {}".format(self.current_step, e)},
                               "return": False}
                self.result_handler.update_class_property(**result_dict)
                self.result_handler.start()
                self.exec_callback(self.__work_around_list_fail)
            if not self.__exec:
                break
            self.current_step += 1
        log.debug("Capture Flag Return : {}".format(flag))
        return flag


class _SwitchThinProMode(PicObjectModel, Window):
    """
    Switch Thinpro Mode with Pic comparison and command with supported
    Use the _SwitchThinProMode instance switch_thinpro_mode to change the mode
    """
    open_window_name = 'hptc-switch-admin'
    close_windows_name = 'hptc-switch-admin',
    is_admin = False
    pic_settings = {
        "admin": ("Test_Data/td_pics/Switch_Thinpro_Mode/admin", (0, 0), ()),
        "domain": ("Test_Data/td_pics/Switch_Thinpro_Mode/domain", (0, 0), ()),
    }

    @classmethod
    def open(cls):
        os.popen('hptc-switch-admin')
        time.sleep(5)

    def window_exists(self):
        first_window_name = 'root password'
        res = subprocess.getoutput(f"wmctrl -l |grep '{first_window_name}'").strip()
        res2 = subprocess.getoutput(f"wmctrl -l |grep '{self.open_window_name}'").strip()
        return True if res or res2 else False

    def __switch_admin(self):
        type_string1 = "1"
        type_string2 = "1"
        exception: Exception = None
        if self.is_admin:
            log.info("Already Admin")
            return
        for i in range(2):
            try:
                self.open()
                if not self.window_exists():
                    raise CaseRunningError(f"{self.open_window_name} not open")
                try:
                    domain = self.domain
                    type_string1 = "root"
                except PicNotFoundError:
                    log.warning("Check Switch Mode is Not Switch to Domain")
                time.sleep(2)
                kb.type_string(type_string1)
                time.sleep(1)
                kb.tap_key(kb.tab_key)
                time.sleep(1)
                kb.type_string(type_string2)
                time.sleep(1)
                kb.tap_key(kb.enter_key)
                time.sleep(2)
                if self.window_exists():
                    raise CaseRunningError(f"Switch Fail At times: {i}")
                log.info("Switch Admin Success")
                self.is_admin = True
                break
            except CaseRunningError as e:
                exception = e
                self.close()
                time.sleep(2)
        else:
            raise exception

    def __switch_user(self):
        self.open()
        for _ in range(2):
            if not self.window_exists():
                break
            self.close()
        log.info("Switch User Success")
        self.is_admin = False

    def __call__(self, switch_to="admin"):
        if switch_to.lower() == "admin":
            self.__switch_admin()
        elif switch_to.lower() == "user":
            self.__switch_user()
        else:
            raise CaseRunningError(f"No Mode {switch_to}")
        return True


class BCUConfig:
    def __init__(self, file):
        """
        Config data expect orderly
        :param file:
        """
        self.file = file
        self.config = self.__analyze_config()

    def __analyze_config(self):
        """
        read bcu config data, and convert to dict
        :return:
        """
        result = {}
        with open(self.file) as f:
            data = f.readlines()
        temp_key = ''
        for line in data:
            if line[0] == '	' or line[0] == ';':
                result[temp_key].append(line.strip())
            else:
                temp_key = line.strip()
                result[temp_key] = []
        return result

    def __save_data(self):
        result = ''
        for k, v in self.config.items():
            result = result + k + '\n'
            for i in v:
                if i and ';' == i[0]:
                    result = result + i + '\n'
                else:
                    result = result + '\t' + i + '\n'
        with open(self.file, 'w') as f:
            f.write(result)

    def enable_values(self, key, values, match=False):
        """
        :param key: strictly match item key in files
        :param values: list: select enabled list of values
        :param match: support key word if match is false, else strictly match value name except capital and small letter
        :return: success return True | not match return False
        """
        for value in values:
            flag = self.enable(key, value, match)
            if flag:
                return True
        return False

    def enable(self, key, value, match=False):
        """
        :param key: strictly match item key in files
        :param value: select enabled value
        :param match: support key word if match is false, else strictly match value name except capital and small letter
        :return: success return True | not match return False
        """
        data = self.config[key]
        result = []
        get_key_flag = False
        for item in data:
            if match:
                if value.upper() == item.upper():
                    result.append('*' + item)
                    get_key_flag = True
                elif value.upper() == item.replace('*', '').upper():
                    return True
                elif item.startswith('*'):
                    result.append(item[1:])
                else:
                    result.append(item)
            else:
                if value.upper() in item.upper():
                    if item.startswith('*'):
                        return True
                    result.append('*' + item)
                    get_key_flag = True
                elif item[0] == '*':
                    result.append(item[1:])
                else:
                    result.append(item)
        if not get_key_flag:
            return False
        self.config[key] = result
        self.__save_data()
        return True

    def reorder(self, key, value, index):
        data = self.config[key]
        for item in data:
            if value.upper() in item.upper():
                data.remove(item)
                data.insert(index - 1, item)
                break
        self.config[key] = data
        self.__save_data()

    def set_value(self, key_word, value, include=None, add=None):
        key = ''
        for k, v in self.config.items():
            if key_word in k:
                key = k
        data = self.config[key]
        if include:
            for d in data:
                if include in d:
                    index = data.index(d)
                    if not add:
                        data[index] = value
                    else:
                        data[index] += value
        else:
            data[0] = value
        self.config[key] = data
        self.__save_data()

    def transform(self, key):
        new_key = ''
        for k, v in self.config.items():
            if key in k:
                new_key = k
        return new_key


switch_thinpro_mode = _SwitchThinProMode.create_object()


class RegistryDescriptor:

    def __init__(self, key, value):
        self.key = key
        self.registry_path = value

    def __get__(self, instance, owner):
        return run_command(f"{instance.base_command_get} {self.registry_path}").strip()

    def __set__(self, instance, value):
        """
        Command: mclient --quiet set + <registry_path> + <value>
        Commands are joined with '&&'
        """
        if instance.command:
            instance.command = f"{instance.command} " \
                             f"{instance.base_glue_string} " \
                             f"{instance.base_command_set} {self.registry_path} '{value}'"
        else:
            instance.command = f"{instance.base_command_set} {self.registry_path} '{value}'"


class RegistryObject:
    """
    This Object describe linux registry information defined in REGISTRY_SETTINGS
    Demonstration:
        Registry = RegistryObject.create_object()
        Registry.AC_standby = 10
        Registry.AC_sleep = 10
        Registry.commit()
        Registry.AC_standby = 20
        Registry.AC_sleep = 20
        Registry.commit()
        # use control_panel_apply command to enable wireless
        Registry.control_panel_apply("enable_wireless")
    """
    registry_settings = REGISTRY_SETTINGS
    base_command_set = "mclient --quiet set"
    base_command_get = "mclient --quiet get"
    base_command_apply = "mclient control_panel_apply"
    base_command_commit = "mclient commit"
    base_glue_string = "&&"

    def __init__(self):
        self.command: str = ""

    def __getattr__(self, key):
        raise CaseRunningError(f"No Such Item '{key}' in REGISTRY_SETTINGS")

    def commit(self):
        """
        Commnad:  <Set Command> && mclient commit
        """
        command = f"{self.command} " \
                  f"{self.base_glue_string} " \
                  f"{self.base_command_commit}"
        run_command(commands=command)
        # reset the command
        self.command = ""

    def apply(self, key: str):
        """
        Command: mclient control_panel_apply <registry_path>
        key: the key in REGISTRY_SETTINGS
        """
        registry_path = REGISTRY_SETTINGS.get(key, "")
        if not registry_path:
            raise CaseRunningError(f"No Such Item '{key}' in REGISTRY_SETTINGS")
        run_command(f"{self.base_command_apply} {registry_path}")

    @classmethod
    def create_object(cls):
        for key, value in REGISTRY_SETTINGS.items():
            setattr(cls, key, RegistryDescriptor(key=key, value=value))
        return cls()


Registry = RegistryObject.create_object()