import os
from numba import jit
import time
import cv2
import math
import shutil
from mss import mss, tools
from Common.common_function import get_folder_items, get_current_dir, VERSION
from Common.log import log
import subprocess
import numpy as np


def capture_screen(file_name, param="-m", auto_fix = False):
    """
    use native method scrot(used in hptc-snipping-tool)
    scrot:
      -b, --border              When selecting a window, grab wm border too
      -c, --count               show a countdown before taking the shot
      -d, --delay NUM           wait NUM seconds before taking a shot
      -e, --exec APP            run APP on the resulting screenshot
      -q, --quality NUM         Image quality (1-100) high value means
                                high size, low compression. Default: 75.
                                For lossless compression formats, like png,
                                low quality means high compression.
      -m, --multidisp           For multiple heads, grab shot from each
                                and join them together.
      -s, --select              interactively choose a window or rectangle
                                with the mouse
      -u, --focused             use the currently focused window
      -t, --thumb NUM           generate thumbnail too. NUM is the percentage
                                of the original size for the thumbnail to be,
                                or the geometry in percent, e.g. 50x60 or 80x20.
      -z, --silent              Prevent beeping
    """
    dir_path = os.path.dirname(file_name)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    if VERSION in ["8.0", ]:
        call = subprocess.Popen("scrot -o {} {}".format(param, file_name), stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, env=os.environ)
    else:
        call = subprocess.Popen("scrot {} {}".format(param, file_name), stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, env=os.environ)
    stdout, stderr = call.communicate(timeout=30)
    # log.debug("[capture]info of capture,out:{},error:{}".format(stdout, stderr))
    if auto_fix:
        img = cv2.imread(file_name)
        n1_f = np.sum(img, axis=2) == 0
        a_g = np.array([102, 102, 102])
        img[n1_f == True] = a_g
        cv2.imwrite(file_name, img)
    return file_name


def capture_screen_mss(file_name):
    dir_path = os.path.dirname(file_name)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with mss() as capture:
        capture.shot(mon=-1, output=file_name)
    return file_name


def capture_screen_by_loc(file_path, loc_dic):
    # loc = {"left": 0, "top": 0, "width": 100, "height": 100}
    with mss() as capture:
        img = capture.grab(monitor=loc_dic)
        tools.to_png(img.rgb, img.size, output=file_path)

def compare_pic_similarity(img, tmp, rate=0.9):
    img_name = cv2.imread(img)
    img_tmp = cv2.imread(tmp)
    t = cv2.matchTemplate(img_name, img_tmp, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(t)
    log.debug("[get pic icon]current match picture: {}, Similarity:{:.3f}/{}".format(img, max_val, rate))
    if max_val > rate:
        return max_loc, img_name.shape
    return False


class WaitElement:

    def __init__(self):
        self._dpi = [1]

    @property
    def dpi(self):
        return self._dpi

    @dpi.setter
    def dpi(self, dpi: list):
        self._dpi = dpi

    def __resize(self, src, size: float):
        return

    def get_icon_by_pic(self, name, offset=(10, 10), rate=0.9, **kwargs):
        """
        find a location in a picture by name
        :param name: path+name
        :param offset: diy a point
        :param rate: a similarity between demo.png and name
        :return: (offset:(x,y),shape:(y,x,3))
        """
        path_demo = get_current_dir('demo.png')
        capture_screen(path_demo)
        template = cv2.imread(path_demo)
        img = cv2.imread(name)
        for dpi in self._dpi:
            if dpi != 1:
                origin_y, origin_x = img.shape[0: 2]
                resize_img = cv2.resize(img, (int(origin_y * dpi), int(origin_x * dpi)), interpolation=cv2.INTER_LINEAR)
            else:
                resize_img = img
            t = cv2.matchTemplate(resize_img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(t)
            log.debug("[get pic icon]current match picture: {}, Resize: {} Similarity:{:.3f}/{}".format(name, dpi, max_val, rate))
            if max_val > rate:
                x = max_loc[0]
                y = max_loc[1]
                return (x + offset[0], y + offset[1]), resize_img.shape
        else:
            return None

    def get_position_by_pic(self, path, offset=(10, 10), **kwargs):
        """
        It's a normal function to get a location
        :param path: picture path
        :param offset: diy a point
        :return: tuple,such as (12,12)
        """
        if isinstance(path, str) and os.path.isdir(path):
            pic_list = get_folder_items(path, file_only=True, filter_name=".png")
            assert pic_list, "pic is not exist in {}".format(path)
            pic_path_list = list(map(lambda x: path + "/{}".format(x), pic_list))
        else:
            pic_path_list = [path, ]
        return self.get_icon_by_pictures(pic_path_list, offset, **kwargs)

    def get_icon_by_pictures(self, name, offset=(10, 10), **kwargs):
        """
        sometimes you have several similar pic,but only
        one picture location will be located
        """
        for pic in name:
            result = self.get_icon_by_pic(name=pic, offset=offset, **kwargs)
            if result:
                return result
        return None

    def wait_element(self, name, cycle=3, offset=(10, 10), **kwargs):
        """
        wait a result by looping
        :param offset:
        :param name: path list or a path which you want to locate a point
        :param cycle: loop number
        :return:
        """
        for i in range(cycle):
            rs = self.get_position_by_pic(name, offset, **kwargs)
            if not rs:
                time.sleep(1)
                continue
            else:
                return rs
        return

    def __call__(self, *args, **kwargs):
        return self.wait_element(*args, **kwargs)


wait_element = WaitElement()


def save_from_data(filename, data):
    dir_path = os.path.dirname(filename)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    cv2.imwrite(filename, data)


def compare_picture_auto_collect(screenshot_file, template_file, auto_fix=False):
    """
    1.check screenshot_file,
    if not exist ,return

    2.check template_file,
    if folder not exist ,create one
    if file not exit ,use source_file

    :param screenshot_file: Full Path
    :param template_file: Full Path
    :return:
    """
    if not os.path.exists(screenshot_file):
        raise Exception("Can not find screenshot_file:{}".format(screenshot_file))

    if not os.path.exists(template_file):
        print("can not find template file:{} ,create a new one".format(template_file))
        dirs = os.path.dirname(template_file)
        if not os.path.exists(dirs):
            os.makedirs(dirs)
        shutil.copyfile(screenshot_file, template_file)
        path, ext = os.path.splitext(template_file)
        shutil.copyfile(screenshot_file, "{}_auto{}".format(path, ext))
    return compare_picture_list(screenshot_file, template_file, auto_fix)


@jit()
def collect_diff_counts(width, height, source, template):
    # i, j are for width and height
    # source is source image
    # template is template image
    diff_count = 0
    for i in range(width):
        for j in range(height):
            if compare_pixel(source[i][j], template[i][j]) > 25:
                diff_count += 1
                source[i][j] = [0, 0, 255]
                continue
    return diff_count, source


def compare_picture(source_file, dest_file, auto_fix=False):
    """
    auto_fix: if background is black, turn it to gray
    """
    source = cv2.imread(source_file)
    dest = cv2.imread(dest_file)
    if auto_fix:
        source = np.asarray(source)
        n1_f = np.sum(source, axis=2) == 0
        a_g = np.array([102, 102, 102])
        source[n1_f == True] = a_g
    w, h = source.shape[0], source.shape[1]

    if source.shape != dest.shape:
        return 0.1, []
    else:
        # if 'linux' in platform.platform().lower():
        #     return 0.99
        # else:
        diff_count, diff_res = collect_diff_counts(w, h, source, dest)
        return 1 - diff_count / (w * h), diff_res


def compare_picture_list(source_file, dest_file, auto_fix=False):
    # source = cv2.imread(source_file)
    # dest = cv2.imread(dest_file)
    # if auto_fix:
    #     source = np.asarray(source)
    #     n1_f = np.sum(source, axis=2) == 0
    #     a_g = np.array([102, 102, 102])
    #     source[n1_f == True] = a_g
    # w, h = source.shape[0], source.shape[1]
    rs = 0, []
    # if source.shape != dest.shape:
    #     rs = 0.1, []
    # else:
    #     diff_count, diff_res = collect_diff_counts(w, h, source, dest)
    #     rs = 1 - diff_count / (w * h), diff_res
    #     if rs[0] > 0.99:
    #         return rs
    # check backup picture
    dest_file = os.path.split(dest_file)
    file_name, extend = dest_file[1].split('.')
    for i in range(5):
        join_name = os.path.join(dest_file[0], '{}{}.{}'.format(file_name, "_{}".format(i) if i else "", extend))
        source = cv2.imread(source_file)
        if auto_fix:
            source = np.asarray(source)
            n1_f = np.sum(source, axis=2) == 0
            a_g = np.array([102, 102, 102])
            source[n1_f == True] = a_g
        dest = cv2.imread(join_name)
        w, h = source.shape[0], source.shape[1]
        if not os.path.exists(join_name):
            continue
        if source.shape != dest.shape:
            continue
        else:
            diff_count, diff_res = collect_diff_counts(w, h, source, dest)
            rs = 1 - diff_count / (w * h), diff_res
            print(rs[0])
            if rs[0] > 0.99:
                return rs
    return rs


@jit()
def compare_pixel(rgb1, rgb2):
    r = (rgb1[0] - rgb2[0])
    g = (rgb1[1] - rgb2[1])
    b = (rgb1[2] - rgb2[2])
    return math.sqrt(r * r + g * g + b * b)


if __name__ == '__main__':
    my_screenshot_file = r"Z:\WorkSpace3\wes_automation_script\temp.png"
    my_template_file = r"Z:\WorkSpace3\wes_automation_script\win10_p1.jpg"
    try:
        my_res = compare_picture_auto_collect(my_screenshot_file, my_template_file)
        print(my_res)
    except Exception as e:
        print(e.args)
