from framework.sources.basefs import Basefs

class Procfs(Basefs):

    def __init__(self):

        super().__init__()

    def name(self):

        return 'procfs'

    def metrics(self):

        metrics = {

            'stat': {
                'type': 'DATA',
                'profiles': [
                    {'nodes': '/proc/stat', 'parser': self.__parse_stat},
                ]
            },

        }

        return metrics

    def __parse_stat(self, output):

        stat = {
            'cpu': dict()
        }

        lines = output.split('\n')

        for line in lines:

            if line[:3] == 'cpu' and line[3] != ' ':

                args = line.split()

                cpu_id = args[0].replace('cpu', '')

                stat['cpu'][cpu_id] = {
                    'user':         int(args[1]),
                    'nice':         int(args[2]),
                    'system':       int(args[3]),
                    'idle':         int(args[4]),
                    'iowait':       int(args[5]),
                    'irq':          int(args[6]),
                    'softirq':      int(args[7]),
                    'steal':        int(args[8]),
                    'guest':        int(args[9]),
                    'guest_nice':   int(args[10])
                }

        return stat