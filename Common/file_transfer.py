import ftplib
import os
import sys

from Common.log import log


class FTPUtils:
    def __init__(self, server, username, password):
        self.ftp = ftplib.FTP(server)
        self.ftp.login(username, password)
        self.download_buffer = 1024
        self.upload_buffer = 1024

    def change_dir(self, work_dir):
        log.info(f"Method 'change_dir', change path to: {str(self.ftp.cwd(work_dir))}")
        return self.ftp.cwd(work_dir)

    def get_working_dir(self):
        log.info(f"Method 'get_working_dir',{str(self.ftp.pwd())}")
        return self.ftp.pwd()

    def get_item_list(self, work_dir):
        self.ftp.cwd(work_dir)
        log.info(f"Method 'get_item_list',path: {str(work_dir)}")
        return self.ftp.nlst()

    def is_item_file(self, item):
        try:
            self.ftp.cwd(item)
            self.ftp.cwd('..')
            return False
        except ftplib.error_perm as fe:
            if not fe.args[0].startswith('550'):
                raise
            return True

    def download_file(self, file_name, save_as_name):
        file_handler = open(save_as_name, 'wb')
        self.ftp.retrbinary("RETR " + file_name, file_handler.write, self.download_buffer)
        file_handler.close()
        return save_as_name

    def download_dir(self, dir_name, save_as_dir):
        if not os.path.exists(save_as_dir):
            os.mkdir(save_as_dir)
            log.info(f"Target folder not exist, create folder: {save_as_dir}")
        self.ftp.cwd(dir_name)
        for item in self.ftp.nlst():
            if self.is_item_file(item):
                self.download_file(item, os.path.join(save_as_dir, item))
                log.info(f"Download file: {str(item)}")
            else:
                self.download_dir(item, os.path.join(save_as_dir, item))
                log.info(f"Download dir: {str(item)}")
        self.ftp.cwd("..")
        return save_as_dir

    def new_dir(self, dir_name):
        try:
            self.ftp.mkd(dir_name)
        except ftplib.error_perm as fe:
            if not fe.args[0].startswith('550'):
                raise fe
            log.info(f"--- has already exists {dir_name}")
        return

    def upload_dir(self, local_dir, remote_dir):
        if not os.path.isdir(local_dir):
            return 
        self.ftp.cwd(remote_dir)
        for file in os.listdir(local_dir):
            two_head_char = file[0:2]
            if "." in two_head_char[0]:
                continue
            elif "__" == two_head_char:
                continue
            src = os.path.join(local_dir, file)
            if os.path.isfile(src):
                self.upload_file(src, file)
            elif os.path.isdir(src):
                try:
                    self.ftp.mkd(file)
                except Exception:
                    log.info(f"has already exists {file}")
                self.upload_dir(src, file)
        self.ftp.cwd("..")
        return
    
    def upload_file(self, local_path, remote_path):
        if not os.path.isfile(local_path):
            return 
        log.info(f"+++ upload {local_path} to {remote_path}")
        self.ftp.storbinary('STOR ' + remote_path, open(local_path, 'rb'), self.upload_buffer)

    def delete_file(self, file_name):
        self.ftp.delete(file_name)
        log.info(f"--- delete file: {file_name}")
        return file_name

    def delete_folder(self, remote_dir):
        self.ftp.cwd(remote_dir)
        lines = []
        self.ftp.retrlines("LIST", callback=lambda x: lines.append(x))
        for line in lines:
            name = line.split(" ")[-1]
            if "<DIR>" in line:
                self.delete_folder(name)
                self.ftp.cwd("..")
                log.info(f"--- delete folder: {name}")
                self.ftp.rmd(name)
            else:
                self.delete_file(name)

    def close(self):
        self.ftp.close()
        log.info("Method 'close'.")


if __name__ == '__main__':
    ftp = FTPUtils(r"15.83.255.102", r"administrator", "Shanghai2010")
    # ftp.download_file(r"ZC_TEST/testpath3.exe","testpath3.exe")
    ftp.upload_file(r"../Test_Report/Site1.yaml","test/Test_Report/Site1.yaml")