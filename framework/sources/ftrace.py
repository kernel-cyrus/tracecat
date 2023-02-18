import os
import sys
import time
import threading
import pandas
import re

from framework.source import Source
from framework.helpers import take_ftrace_buffer
from framework.executors.adb_executor import Adb_executor
from framework.config import CONFIG

class Ftrace(Source):

    def __init__(self):

        super().__init__()

        self.events = set()

        self.df = None

        self.wait_num = 0

        self.wait_num_mutex = threading.Lock()

    def _name(self):

        return 'ftrace'

    def _enable(self, item):

        self.events.add(item)

    def __init_instance(self):

        self.ftrace_instance = '/sys/kernel/tracing'

        try:

            # Try to use global buffer first

            take_ftrace_buffer('ftrace')

        except:

            # Try to create unique instance

            self.ftrace_instance = '/sys/kernel/tracing/instances/tracecat'

            executor = Adb_executor()

            if not executor.connect():

                sys.exit('ERROR: Adb device not found.')

            errors = executor.exec('mkdir %s' % self.ftrace_instance)

            # Trigger the exception

            if 'Permission denied' in errors:

                sys.exit('ERROR: Can\'t enable ftrace instance, you may need root authority.')

    def _pre_trace(self, duration):

        self.__init_instance()

        self.__reset_ftrace()

    def __reset_ftrace(self, executor = None):

        if not executor:

            executor = Adb_executor()

            if not executor.connect():

                sys.exit('ERROR: Adb device not found.')

        executor.exec('echo boot > %s/trace_clock' % self.ftrace_instance)

        executor.exec('echo 0 > %s/tracing_on' % self.ftrace_instance)

        executor.exec('echo > %s/trace' % self.ftrace_instance)

        executor.exec('echo > %s/set_event' % self.ftrace_instance)

        executor.exec('echo %s > %s/buffer_size_kb' % (CONFIG['FTRACE_BUFFER_SIZE'], self.ftrace_instance))

    def _trace(self, duration):

        executor = Adb_executor()

        executor.connect()

        local_file = self.get_workspace() + 'ftrace.data'

        remote_file = CONFIG['REMOTE_ROOT'] + '/ftrace/ftrace.data'

        print('Start ftrace...')

        self.__reset_ftrace(executor)

        executor.exec('mkdir ' + os.path.dirname(remote_file))

        # Enable ftrace events

        for event in self.events:

            errors = executor.exec('echo %s >> %s/set_event' % (event, self.ftrace_instance))

            if 'Permission denied' in errors:

                sys.exit('ERROR: Can\'t set ftrace events, you may need root authority.')

        events = executor.exec('cat %s/set_event' % self.ftrace_instance)

        events = events.split()

        for event in self.events:

            if event not in events:

                sys.exit('ERROR: Invalid ftrace event: %s' % event)

        # Start tracing

        executor.exec('rm -rf %s' % remote_file)

        executor.exec('echo 1 > %s/tracing_on' % self.ftrace_instance)

        executor.exec('timeout %s cat %s/trace_pipe > %s; sync' % (duration + 1, self.ftrace_instance, remote_file))

        self.__reset_ftrace(executor)

        # Get files back

        print('Fetching ftrace data file...')

        executor.pull(remote_file, local_file)

        print('Done. (%s)' % local_file)

    def _parse(self):
        
        raw_file = self.get_workspace() + 'ftrace.data'

        pkl_file = self.get_workspace() + 'ftrace.pkl'

        if not os.path.exists(raw_file):

            sys.exit('ERROR: Ftrace data file not found.')

        if not os.path.exists(pkl_file):

            self.df = self.__load_raw_file(raw_file)

            print('Saving ftrace data to pickle...')

            self.df.to_pickle(pkl_file)

            self.df.to_excel(pkl_file[:-4] + '.xlsx')

        else:

            print('Loading ftrace data from pickle...')

            self.df = self.__load_pkl_file(pkl_file)

    def __load_raw_file(self, file_path):

        results = {
            'task': list(),
            'pid': list(),
            'cpu': list(),
            'status': list(),
            'timestamp': list(),
            'function': list(),
            'data': list(),
        }

        with open(file_path, 'r') as file:

            lines = file.readlines()

            total = len(lines)

            count = 0

            share = int(total / 100)

            for line in lines:

                if total > 100000 and count % share == 0:
                    print('\rProcessing... (%d%%)' % (count / share), end='', flush=True)

                if not line:
                    continue

                try:

                    cpu_match = re.search('\[[0-9]{3}\]', line).span()

                    part_a = line[:cpu_match[0]]

                    part_b = line[cpu_match[1]:]

                    args_a = part_a.rsplit('-', 1)

                    args_b = part_b.split(None, 2)

                    results['task'].append(args_a[0].strip())

                    results['pid'].append(args_a[1].strip())

                    results['cpu'].append(int(line[cpu_match[0]+1:cpu_match[1]-1]))

                    results['status'].append(args_b[0])

                    results['timestamp'].append(int(float(args_b[1][:-1]) * 1000000000))

                    parts = args_b[2].split(':', 1)

                    results['function'].append(parts[0])

                    results['data'].append(parts[1].strip())

                except Exception as e:

                    if 'LOST' in line and 'EVENTS' in line:
                        print('WARNING: Ftrace data lost, try enlarge the ftrace buffer size.')
                    else:
                        sys.exit('ERROR: Parsing ftrace data line error:\n%s%s' % (line, e))

                count += 1

            print('\rOK. (%d rows parsed)' % total)

        return pandas.DataFrame(results)

    def __load_pkl_file(self, file_path):

        return pandas.read_pickle(file_path)

    def wait_trace_on(self):

        self.wait_num_mutex.acquire()

        first_waiter = self.wait_num == 0

        self.wait_num += 1

        self.wait_num_mutex.release()

        executor = Adb_executor()

        executor.connect()

        for cnt in range(0, 30):

            trace_on = int(executor.exec('cat %s/tracing_on' % self.ftrace_instance))

            if trace_on:

                time.sleep(0.1)

                if first_waiter and cnt > 0:
                    print('Trace start...')

                return True

            if first_waiter and cnt == 0:
                print('Waiting for ftrace on...')

            time.sleep(0.1)

        return False

    def get_data(self, task = None, pid = None, cpu = None, function = None, start_time = None, end_time = None):

        df = self.df.copy()

        if task is not None:

            df = df[df.task == task]

        if pid is not None:

            df = df[df.pid == pid]

        if cpu is not None:

            df = df[df.cpu == cpu]

        if function is not None:

            df = df[df.function == function]

        if start_time is not None:

            df = df[df.timestamp >= start_time]

        if end_time is not None:

            df = df[df.timestamp <= end_time]

        return df
