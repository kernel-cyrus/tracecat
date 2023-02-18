import os

from ppadb.client import Client as Adb_Client

from framework.executor import Executor
from framework.config import CONFIG

class Adb_executor(Executor):

    def __init__(self):

        self.client = Adb_Client()

    def connect(self, addr = None, port = None, username = None, password = None):

        try:
            devices = self.client.devices()

        except:

            os.system('adb start-server') # start up adb service

            devices = self.client.devices()

        self.device = devices[0] if devices else None

        return True if self.device else False

    def exec(self, command, handler = None):

        return self.device.shell(cmd = 'su -c ' + command if CONFIG['EXEC_WITH_SU'] else command, handler = handler)

    def push(self, local, remote):

        return self.device.push(local, remote)

    def pull(self, remote, local):

        return self.device.pull(remote, local)

    @staticmethod
    def print_handler(connection):

        while True:

            data = connection.read(1024)

            if not data:

                break

            print(data.decode('utf-8'), end='')

        connection.close()