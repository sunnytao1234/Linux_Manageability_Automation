import shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import zipfile
import os
from jinja2 import Environment, FileSystemLoader
import pandas
import yaml

from Common.common_function import get_current_dir, check_ip_yaml
from Common.log import log
import socket
from Common.support_design_report_style import zip_file_name,get_report_value,get_report_number


class GenerateReport:
    def __init__(self, start, end):
        self.__test_report_root = get_current_dir('Test_Report')
        self.__template_folder = get_current_dir('Test_Data', 'td_report')
        self.__static_src = get_current_dir('Test_Data', 'td_report', 'static')
        self.__name = 'report'
        self.ip = check_ip_yaml()
        self.__start_time = start
        self.__end_time = end
        self.__load_uut_result()
        self.__data_by_case = self.__generate_table()
        self.total = {
            'Passing rate': '%.2f' % (100 * self.__data_by_case['passCount'] / self.__data_by_case['count']),
            'Pass': self.__data_by_case['passCount'],
            'Fail': self.__data_by_case['failCount'],
            'NoRun': self.__data_by_case['norunCount'],
            'Count': self.__data_by_case['count']
        }
        self.pie_chart_data = [
            {
                'value': self.total['Pass'],
                'name': 'Pass',
                'itemStyle': {'color': '#5cb85c'}
            },
            {
                'value': self.total['Fail'],
                'name': 'Fail',
                'itemStyle': {'color': '#d9534f'}
            },
        ]
        self.framework_version = '1.0'
        self.script_version = '1.0'
        pass

    def generate(self):
        env = Environment(loader=FileSystemLoader(
            os.path.join(os.getcwd(), self.__template_folder), encoding='utf-8'))
        template = env.get_template('template_report_content.html')
        html = template.render(task_name=self.__name,
                               framework_version=self.framework_version,
                               script_version=self.script_version,
                               start=self.__start_time,
                               end=self.__end_time,
                               final_data=self.__data_by_case['final_data'],
                               final_data_2=self.__data_by_case['final_data'],
                               data=self.pie_chart_data,
                               total=self.total,
                               encoding='utf-8')  # unicode string
        with open(get_current_dir('Test_Report', 'report.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        # copy static folder
        if self.__get_src_files():
            log.info('generate {}.html finished'.format(self.__name))
        return self.__test_report_root

    def __get_src_files(self):
        static_path = os.path.join(os.getcwd(), self.__static_src)
        if os.path.exists(get_current_dir('Test_Report', 'static')):
            shutil.rmtree(get_current_dir('Test_Report', 'static'))
            log.info('Target static folder exist, remove the old folder')
        shutil.copytree(static_path, get_current_dir('Test_Report', 'static'))
        log.info('Copy static folder to report folder finished')
        return True

    def __generate_table(self):
        test_result_file = get_current_dir('Test_Report', '{}.yaml'.format(self.ip))
        with open(test_result_file, 'r') as f:
            source_data = yaml.safe_load(f)
            for i in source_data:
                i['result'] = i['result'].lower()
        df_raw = pandas.DataFrame(source_data)
        # remove the unnecessary column
        df_new = df_raw[['case_name', 'result']]
        table_raw = pandas.pivot_table(df_new, index='case_name', columns='result', aggfunc=len, fill_value=0,
                                       margins=True)
        # Turn index to new column
        table_raw['case_name'] = table_raw.index
        if 'fail' not in table_raw.keys():
            table_raw['fail'] = 0
        if 'pass' not in table_raw.keys():
            table_raw['pass'] = 0
        table_format = table_raw[['case_name', 'pass', 'fail']]
        # raw_data: list:[[key_name, 'pass_count', 'fail_count'], [key_name, 'pass_count', 'fail_count'], ...]
        raw_data = table_format.values.tolist()
        final_data = []
        data_dict = {}

        for item in raw_data[:-1]:
            current_case_list = []
            for each_result in source_data:
                if item[0] == each_result['case_name']:
                    current_case_list.append(each_result)
            final_data.append([item[0], current_case_list, item[1], item[2], 0, item[1] + item[2]])
        # get last created_item in list
        total_item = raw_data.pop()
        data_dict['final_data'] = final_data
        data_dict['passCount'] = total_item[1]
        data_dict['failCount'] = total_item[2]
        data_dict['norunCount'] = 0
        data_dict['count'] = total_item[1] + total_item[2]
        return data_dict

    def __load_uut_result(self):
        result_file = get_current_dir('Test_Report', '{}.yaml'.format(self.ip))
        if not os.path.exists(result_file):
            empty_result = [{
                'uut_name': self.ip,
                'case_name': 'No result return',
                'steps': [],
                'result': 'fail'
            }, {
                'uut_name': self.ip,
                'case_name': 'No result return',
                'steps': [],
                'result': 'pass'
            }]
            log.error('Result File {} Not Exsit'.format(result_file))
            result = empty_result
        else:
            with open(result_file, encoding='utf-8') as f:
                result = yaml.safe_load(f.read())
        try:
            self.return_to_ALM(result)
        except Exception as e:
            log.error('Fail to return result to ALM:')
            log.error(str(e))
        return result


def zip_dir(skip_img=True):
    """
    压缩指定文件夹
    :param dirpath: 目标文件夹路径
    :param outFullName: 压缩文件保存路径+xxxx.zip
    :return: 无
    """

    newfilename = str(zip_file_name(get_report_number(), get_report_value()))
    filename = get_current_dir('{}.zip').format(newfilename)
    # filename = get_current_dir('report.zip')
    zip = zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(get_current_dir('Test_Report')):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(get_current_dir('Test_Report'), '')
        if 'img' in dirnames:
            if skip_img:
                dirnames.remove('img')
        for name in filenames:
            zip.write(os.path.join(path, name), os.path.join(fpath, name))
    zip.close()
    return filename


def getAttachment(attachmentFilePath):
    attachment = MIMEText(open(attachmentFilePath, 'rb').read(), 'base64', 'utf-8')
    attachment["Content-Type"] = 'application/octet-stream'
    attachment["Content-Disposition"] = 'attachment;filename=%s' % os.path.basename(attachmentFilePath)
    return attachment


def send_mail(recipient, subject='Automation Report Linux', text='', attachment=''):
    mailUser = "AutomationTest<AutoTest@hp.com>"
    msg = MIMEMultipart('related')
    msg['From'] = mailUser
    msg['To'] = ','.join(recipient)
    msg['Subject'] = subject  # "AddonCatalog check result"
    msg.attach(MIMEText(text, 'html', 'utf-8'))
    if attachment:
        msg.attach(getAttachment(attachment))
    try:
        mailServer = smtplib.SMTP(host='15.73.212.81', port=25, local_hostname=socket.gethostname())
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.sendmail(mailUser, recipient, msg.as_string())
        mailServer.close()
        log.info("Sent email to %s success" % recipient)
    except:
        import traceback
        log.info(traceback.format_exc())


def generate_text():
    def read_yaml(yaml_file):
        with open(yaml_file, 'r') as f:
            source_data = yaml.safe_load(f)
            if not source_data:
                source_data = []
        data_lis = []
        for case in source_data:
            case_info = [case['case_name'], case['result']]
            for step in case['steps']:
                if step['result'].upper() == 'FAIL':
                    case_info.append(f"{step['step_name']}")
                    case_info.append(f"""Expect:<br>{step['expect']}<br>
                                        Actual:<br>{step['actual']}<br>
                                        Note:<br>{step['note']}""")
                    break
            else:
                case_info.append("")
                case_info.append("")

            data_lis.append(case_info)
        return data_lis

    result_path = get_current_dir(f'Test_Report/{check_ip_yaml()}.yaml')
    result = read_yaml(result_path)
    if not result:
        return ''

    def add_string(i):
        html_info = """
                <tr>   

                        <td text-align="center">{index} </td>

                        <td>{case_name} </td>

                        <td><font color={color}>{status} </font></td>

                        <td>{actual} </td>

                        <td>{node} </td>

                </tr>
                """
        color = "Green"
        if i[1].upper() == 'FAIL':
            color = "red"
        return html_info.format(color=color, index=result.index(i) + 1, case_name=i[0],
                                status=i[1], actual=i[2], node=i[3])

    text = """
           <table color="CCCC33" border="1" cellspacing="0" cellpadding="5" text-align="center">
    
                   <tr bgcolor="LightSkyBlue" style="font-weight:bold;vertical-align:middle;text-align:center;">
    
                           <td>Index</td>
    
                           <td>Test Unit</td>
    
                           <td>Status</td>
    
                           <td>Fail Step</td>
    
                           <td>Note</td>
    
                   </tr>   
    
                   {result}
    
           </table>""".format(result=''.join(map(add_string, result)))

    return text


if __name__ == "__main__":
    # main(sys.argv)
    zip_dir()
    pass
