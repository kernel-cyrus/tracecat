import os
import sys
import platform

from perfetto.trace_processor import TraceProcessor

from framework.source import Source
from framework.helpers import get_runtime_path, take_ftrace_buffer
from framework.executors.adb_executor import Adb_executor
from framework.config import CONFIG

class Perfetto(Source):

    def __init__(self):

        super().__init__()

        self.config = self.__init_config()

        self.processor = None

        self.enabled = set()

    def __del__(self):

        if self.processor:

            self.processor.close()

    def __get_path(self, file):

        paths = {
            'loc_trace':  self.get_workspace() + 'perfetto.trace',
            'loc_config': self.get_workspace() + 'perfetto.config',
            'dev_trace':  '/data/misc/perfetto-traces/trace'
        }

        return paths[file]

    def __init_config(self):

        config = ''

        runtime_path = get_runtime_path()

        config_file = runtime_path + '/configs/perfetto/perfetto.conf'

        if not os.path.exists(config_file):

            sys.exit('ERROR: Perfetto config file is missing.')

        with open(config_file, 'r') as file:

            lines = file.readlines()

            for line in lines:

                if 'duration_ms:' not in line:

                    config += line

        return config

    def __set_config(self, config):

        self.config += config

    def __get_config(self, duration):

        return self.config + 'duration_ms: %d' % (duration * 1000)

    def _name(self):

        return 'perfetto'

    def enable(self, item = None):

        take_ftrace_buffer('perfetto')

        super().enable(item)

    def _enable(self, item):

        if item in self.enabled:

            return

        self.enabled.add(item)

        if item == 'sched':

            self.__set_config('''
data_sources: {
    config {
        name: "linux.process_stats"
        target_buffer: 1
        process_stats_config {
            scan_all_processes_on_start: true
        }
    }
}
data_sources: {
    config {
        name: "linux.ftrace"
        ftrace_config {
            ftrace_events: "sched/sched_switch"
            ftrace_events: "power/suspend_resume"
            ftrace_events: "sched/sched_wakeup"
            ftrace_events: "sched/sched_wakeup_new"
            ftrace_events: "sched/sched_waking"
            ftrace_events: "sched/sched_process_exit"
            ftrace_events: "sched/sched_process_free"
            ftrace_events: "task/task_newtask"
            ftrace_events: "task/task_rename"
            ftrace_events: "sched/sched_blocked_reason"
            buffer_size_kb: 2048
            drain_period_ms: 250
        }
    }
}'''.strip() + '\n')

        elif item == 'cpu_freq':

            self.__set_config('''
data_sources: {
    config {
        name: "linux.ftrace"
        ftrace_config {
            ftrace_events: "power/cpu_frequency"
            ftrace_events: "power/suspend_resume"
            buffer_size_kb: 2048
            drain_period_ms: 250
        }
    }
}'''.strip() + '\n')

        elif item == 'cpu_idle':

            self.__set_config('''
data_sources: {
    config {
        name: "linux.ftrace"
        ftrace_config {
            ftrace_events: "power/cpu_idle"
            ftrace_events: "power/suspend_resume"
            buffer_size_kb: 2048
            drain_period_ms: 250
        }
    }
}'''.strip() + '\n')
    
        else:
            self.enabled.remove(item)

    def _trace(self, duration):

        executor = Adb_executor()

        if not executor.connect():

            sys.exit('ERROR: Adb device not found.')

        executor.exec('setprop persist.traced.enable 1') # enable trace service

        # save config file

        config = self.__get_config(duration)

        with open(self.__get_path('loc_config'), 'w') as file:

            file.write(config)

        # start tracing

        print('Start tracing...')

        ret_a = executor.exec('ls -l %s' % self.__get_path('dev_trace'))

        execute_su = 'su -c' if CONFIG['EXEC_WITH_SU'] else ''

        os.system('adb shell %s perfetto --txt -c - -o %s < %s' % (execute_su, self.__get_path('dev_trace'), self.__get_path('loc_config')))

        #FIXME: temporary use os.system, exec cant run well on OPPO reno4
        #executor.exec('perfetto --txt -c - -o %s <<EOF\n %s \nEOF' % (self.__get_path('dev_trace'), config), handler = executor.print_handler)

        ret_b = executor.exec('ls -l %s' % self.__get_path('dev_trace'))

        if ret_a == ret_b or not int(ret_b.split()[4]):

            sys.exit('ERROR: Failed. Please check error message.')

        print('Fetching trace file...')

        executor.pull(self.__get_path('dev_trace'), self.__get_path('loc_trace'))

        print('Done. (%s)' % self.__get_path('loc_trace'))

    def _parse(self):
        
        runtime_path = get_runtime_path()
        
        bin_path = None

        if platform.system() == 'Windows':

            bin_path = runtime_path + '/libs/perfetto/windows-amd64/trace_processor_shell.exe'

        elif platform.system() == 'Linux':

            bin_path = runtime_path + '/libs/perfetto/linux-amd64/trace_processor_shell'

        elif platform.system() == 'Darwin':

            bin_path = runtime_path + '/libs/perfetto/mac-amd64/trace_processor_shell'

        if not self.processor:

            if platform.system() != 'Windows':

                os.system('chmod a+x %s' % bin_path)
            
            self.processor = TraceProcessor(bin_path=bin_path, file_path=self.__get_path('loc_trace'))

    def query(self, sql):

        results = list()

        objects = self.processor.query(sql)

        for obj in objects:
            
            if len(results) >= 100000 and len(results) % 100 == 0:

                print('\rProcessing... (%d)' % len(results), end='', flush=True)

            results.append(obj.__dict__.copy())

        if len(results) >= 100000:

            print('\rOK. (%d)          ' % len(results)) # Use space to overwrite exsit text

        return results

    def get_trace_info(self):

        trace_info = {}

        # Get trace time info

        query = 'select min(ts) as start_time, max(ts) as end_time from counter'

        df = self.processor.query(query).as_pandas_dataframe()

        # If counter is empty, try to get trace time from sched table

        if df.iloc[0]['start_time'] is None or df.iloc[0]['end_time'] is None:

            query = 'select min(ts) as start_time, max(ts_end) as end_time from sched'

            df = self.processor.query(query).as_pandas_dataframe()

        if df.iloc[0]['start_time'] is None or df.iloc[0]['end_time'] is None:

            sys.exit('ERROR: Failed to parse trace start / end time from perfetto trace.')

        trace_info['start_time'] = int(df.iloc[0]['start_time'])
        trace_info['end_time']   = int(df.iloc[0]['end_time'])
        trace_info['duration']   = trace_info['end_time'] - trace_info['start_time']

        # Get trace cpu info

        query = 'select distinct(cpu) as cpu from cpu_counter_track order by cpu asc'

        df = self.processor.query(query).as_pandas_dataframe()

        # If counter is empty, try to get trace time from sched table

        if not df['cpu'].tolist():

            query = 'select distinct(cpu) as cpu from sched order by cpu asc'

            df = self.processor.query(query).as_pandas_dataframe()

        if not df['cpu'].tolist():

            sys.exit('ERROR: Failed to parse cpu list from perfetto trace.')

        trace_info['cpu_list'] = df['cpu'].tolist()

        # Done

        return trace_info