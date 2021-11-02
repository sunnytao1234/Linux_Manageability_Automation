class FileNotExistError(Exception):
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class AnalyzeNameError(Exception):
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class LogonError(Exception):
    """
        LogonError
    """
    pass


class ServerNotExitError(LogonError):
    '''
        ClientError
    '''
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return "Failed to check the initial destination server:" + self.s


class AuthenticationError(LogonError):
    '''
        ClientError
    '''
    def __init__(self, s="Authentication failure, check credentials:"
                         "\r\ncheck usr, domain, password"):
        self.s = s

    def __str__(self):
        return self.s


class ClientSeverError(LogonError):
    '''
        ClientError
    '''
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class CertificationError(LogonError):
    '''
        ClientError
    '''
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class VDILogonError(LogonError):
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class CreateVDIError(LogonError):
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class DeleteVDIError(LogonError):
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class Continue(LogonError):
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class LogoffError(Exception):
    """
    LogoffError
    """


class SocketError(LogoffError):
    """
    SocketError
    """
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class ConnectionRefused(LogoffError):
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class LogoffTimeout(LogoffError):
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class IconNotExistError(Exception):
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class MemoryNotSufficient(Exception):
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class CaseRunningError(Exception):
    """
    Main Error at Case Running
    """
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class PicOperatorError(CaseRunningError):
    """
    Extend it if you want to operate elements
    """


class ClickError(PicOperatorError):
    pass


class PathNotFoundError(CaseRunningError):
    pass


class PicNotFoundError(CaseRunningError):
    """
    Can't find Pic at CaseRunning
    """


class RestoreEnvironmentError(Exception):
    def __init__(self, s=""):
        self.s = s

    def __str__(self):
        return self.s


class TimeOutError(CaseRunningError):
    pass


class NoAvailableStaticIP(CaseRunningError):
    pass