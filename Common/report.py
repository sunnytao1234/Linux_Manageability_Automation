from Common import common_function
import os
import yaml,sys
from Common.common_function import argv_filter


class Report:
    def __init__(self, case_name):
        self.result = "Pass"
        # self.uut_name = "NA"
        # self.script_complete_path = self.get_script_complete_path()
        self.script_complete_path = common_function.get_current_dir()
        self.case_name = case_name
        # self.get_ip = self.get_ip()
        self.ip = common_function.get_ip()
        self.uut_name = self.ip
        self.report_path = self.get_report_path()
        self.steps_value_list = []

    def get_report_path(self):
        # script_directory = os.path.split(os.path.splitext(self.script_complete_path)[0])[0]
        report_path = "{0}/Test_Report/{1}.yaml".format(self.script_complete_path, self.ip)
        argvs = sys.argv
        if argvs[1:]:
            site, host_list, user, password, *params = argv_filter(argvs)
            report_path = os.path.join(os.path.split(report_path)[0], "{}.yaml".format(site))
        return report_path

    def reporter(self, step_name='', result='', expect='', actual='', note=''):
        if result.upper() == "FAIL":
            self.result = "FAIL"
        dic = {"step_name": step_name, "result": result, "expect": expect, "actual": actual,
               "note": note}  # The dic of one step
        self.steps_value_list.append(dic)
        return self.steps_value_list

    def generate(self):
        report_data = []
        case_dic = {"case_name": self.case_name, "result": self.result, "steps": self.steps_value_list,
                    "uut_name": self.uut_name}  # The data of one case.
        report_data.append(case_dic)

        if not os.path.exists(self.report_path):
            self.write_data_to_yaml(report_data)  # Write data to yaml file
        else:
            original_data = self.get_original_data()
            if original_data is not None:
                new_data = original_data + report_data
            else:
                new_data = report_data
            self.write_data_to_yaml(new_data)  # Write data to yaml file

    def write_data_to_yaml(self, data):
        # if not os.path.exists(self.report_path):
        with open(self.report_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f)

    def get_original_data(self):
        with open(self.report_path, 'r', encoding='utf-8') as f:
            original_data = yaml.safe_load(f)
            return original_data
