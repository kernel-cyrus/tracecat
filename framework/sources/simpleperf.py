import os
import sys
import time
import pandas

from framework.source import Source
from framework.executors.adb_executor import Adb_executor
from framework.config import CONFIG

class Simpleperf(Source):

    def __init__(self):

        super().__init__()

        self.events = set()

        self.period = 500 # use 500ms as default interval

        self.app = None

        self.df = None

    def invoke_sources(self):

        self.ftrace = self.invoke_source('ftrace', 'sched:sched_process_exec')

    def _name(self):

        return 'simpleperf'

    def _enable(self, item):

        self.events.add(item)

    def _trace(self, duration):

        executor = Adb_executor()

        if not executor.connect():

            sys.exit('ERROR: Adb device not found.')

        local_file = self.get_workspace() + 'simpleperf.data'

        remote_file = CONFIG['REMOTE_ROOT'] + '/simpleperf/simpleperf.data'

        print('Start simpleperf...')

        # Wait for tracing on

        ret = self.ftrace.wait_trace_on()

        if not ret:

            sys.exit('ERROR: Wait for ftrace on timeout.')

        # Start simpleperf

        executor.exec('mkdir ' + os.path.dirname(remote_file))

        if self.app:    # App Mode
            # NOTE: remove --use-devfreq-counters for compatibility
            errors = executor.exec('simpleperf stat --app %s -e %s --interval %d --duration %d -o %s' % (self.app, ','.join(self.events), self.period, duration, remote_file))
        else:           # Global Mode
            # NOTE: remove --use-devfreq-counters for compatibility
            errors = executor.exec('simpleperf stat -a -e %s --per-core --interval %d --duration %d -o %s' % (','.join(self.events), self.period, duration, remote_file))

        if errors:

            if 'multiplexing' in errors:
                print('WARNING: Simpleperf: Some events only run a subset of enabled time, using hardware counter multiplexing.')
            else:
                sys.exit('ERROR: Simpleperf error: ' + errors.strip())

        # Fetch perf data back

        print('Fetching simpleperf data file...')

        executor.pull(remote_file, local_file)

        print('Done. (%s)' % local_file)

    def _parse(self):
        
        raw_file = self.get_workspace() + 'simpleperf.data'

        pkl_file = self.get_workspace() + 'simpleperf.pkl'

        if not os.path.exists(pkl_file):

            self.df = self.__load_raw_file(raw_file)

            print('Saving simpleperf data to pickle...')

            self.df.to_pickle(pkl_file)

            self.df.to_excel(pkl_file[:-4] + '.xlsx')

        else:
            print('Loading simpleperf data from pickle...')

            self.df = self.__load_pkl_file(pkl_file)

    def __get_start_timestamp(self):

        df = self.ftrace.get_data(task='simpleperf', function='sched_process_exec')

        if df.empty:

            # Fallback to search all task
            df = self.ftrace.get_data(function='sched_process_exec')

            df = df[df['data'].str.startswith('filename=/system/bin/simpleperf')]

        if len(df) != 1:

            sys.exit('ERROR: Can\'t get simpleperf timestamp data.')

        ts = df.iloc[0].timestamp

        ts_fix = 27 * 1000000 # adjust real start time for 27ms

        return ts + ts_fix

    def __load_raw_file(self, file_path):

        results = {
            'timestamp': list(),
            'cpu': list(),
            'event': list(),
            'count': list(),
            'count_normalize': list(),
            'runtime_percent': list(),
            'remark': list(),
        }

        start_time = self.__get_start_timestamp()

        prev_count = dict()

        with open(file_path, 'r') as file:

            lines = file.readlines()

            for line in lines:

                if not line.strip():

                    continue

                if line.lstrip()[0] == '#': # Confirm data format by parsing the headline

                    columns = line.split()

                    per_cpu = True if columns[1] == 'cpu' else False # If we have per cpu data (app mode or global mode)

                elif line.lstrip()[0].isnumeric():

                    if per_cpu:

                        l_parts = line.split(None, 4)

                    else:

                        l_parts = line.split(None, 3)

                        l_parts.insert(0, None)

                    cpu = l_parts[0]

                    count = int(l_parts[1].replace(',', ''))

                    event = l_parts[2]

                    r_parts = l_parts[4].rsplit(None, 1)

                    if len(r_parts) == 1: # count/runtime data may not exsist

                        r_parts.insert(0, None)

                    remark = r_parts[0]

                    runtime_percent = float(r_parts[1][1:-2]) / 100

                    results['cpu'].append(cpu)

                    results['event'].append(event)

                    results['remark'].append(remark)

                    results['runtime_percent'].append(runtime_percent)

                    if event not in prev_count:

                        prev_count[event] = dict()

                    if cpu not in prev_count[event]:

                        prev_count[event][cpu] = 0

                    count_delta = count - prev_count[event][cpu]

                    results['count'].append(count_delta)

                    count_normalize = int(count_delta / runtime_percent)

                    results['count_normalize'].append(count_normalize)

                    prev_count[event][cpu] = count

                elif line[:16] == 'Total test time:':

                    cells = len(results['event']) - len(results['timestamp'])

                    timestamp = int(float(line[17:].split()[0]) * 1000000000) + start_time

                    results['timestamp'].extend([timestamp] * cells)

        df = pandas.DataFrame(results)

        df.sort_values(['timestamp', 'event', 'cpu'], inplace=True)

        df.reset_index(drop=True, inplace=True)

        return df

    def __load_pkl_file(self, file_path):

        return pandas.read_pickle(file_path)

    def set_period(self, period):

        if period:

            self.period = period

    def set_app(self, app):

        if app:

            self.app = app

    def get_data(self, event = None, cpu = None, start_time = None, end_time = None):

        df = self.df.copy()

        if type(event) is str:

            df = df[df.event == event]

        if type(event) is list:

            df = df[df.event.isin(event)]

        if cpu is not None:

            df = df[df.cpu == cpu]

        if start_time is not None:

            df = df[df.timestamp >= start_time]

        if end_time is not None:

            df = df[df.timestamp <= end_time]

        return df
