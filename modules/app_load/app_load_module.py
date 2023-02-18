import sys
import pandas

from framework.module import Module
from framework.helpers import sub_slices, get_time, pick_next_window, get_unique_list

class App_load_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'app_load'

    def get_desc(self):

        return 'Process cpu usage on each core. (Parse from trace)'

    def get_help(self):

        text = '''
    某个进程的CPU占用率
    
    > tracecat "trace:app_load"                  # 抓取perfetto trace
    > tracecat "parse:app_load"                  # 解析app_load
    > tracecat "parse:app_load(100ms)"           # 以100ms粒度解析app_load
    > tracecat "chart:app_load"                  # 显示所有process
    > tracecat "chart:app_load(1532)"            # 显示所有pid为1532的进程各核占用率
    > tracecat "chart:app_load(pubg)"            # 显示名字包含pubg的进程各核占用率

    * 不建议长时间抓取，因为生成的trace文件可能过大'''

        return text

    def invoke_sources(self):

        self.perfetto = self.invoke_source('perfetto', 'sched')

    def __get_process_list(self):

        results = self.perfetto.query('select upid, pid, name from process')

        return results

    def __get_sched_slices(self):

        return self.perfetto.query('select s.cpu cpu_id, s.ts start_time, s.ts_end end_time, s.dur duration, t.utid, t.tid, p.upid, p.pid from sched as s join thread as t on t.utid=s.utid join process as p on p.upid=t.upid where s.utid > 0 order by s.ts asc')

    def do_parse(self, params):

        results = list()

        window = None

        window_time = get_time(params[0], 'ms') * 1000000 if params else 1000 * 1000000

        trace_info = self.perfetto.get_trace_info()

        process_list = self.__get_process_list()
        
        sched_slices = self.__get_sched_slices()

        while window := pick_next_window(window, trace_info['start_time'], trace_info['end_time'], window_time, True):

            # init window records

            records = dict()

            for proc in process_list:

                records[proc['upid']] = {
                    'timestamp': window['end'],
                    'proc_id': proc['pid'],
                    'proc_name': proc['name']
                }

                for cpu_id in trace_info['cpu_list']:

                    records[proc['upid']]['cpu_time_' + str(cpu_id)] = 0
                    records[proc['upid']]['cpu_load_' + str(cpu_id)] = 0

            # get each process cpu load

            slices = sub_slices(sched_slices, window['start'], window['end'])

            for row in slices:

                records[row['upid']]['cpu_time_' + str(row['cpu_id'])] += row['duration']

            for record in records.values():

                for cpu_id in trace_info['cpu_list']:

                    record['cpu_load_' + str(cpu_id)] = int((record['cpu_time_' + str(cpu_id)] / window_time) * 10000) / 100
            
            # append to results
            results += records.values()

        columns = ['timestamp', 'proc_id', 'proc_name'] + ['cpu_load_' + str(cpu_id) for cpu_id in trace_info['cpu_list']]

        return pandas.DataFrame(results, columns = columns)

    def __get_proc_list(self, df):

        proc_list = get_unique_list(df, {'proc_id': int, 'proc_name': str}, skip_none = True) # None means interrupt, skip it.

        return sorted(proc_list, key = lambda i: i['proc_id'])

    def __print_proc_list(self, proc_list):

        print('Process:')

        for proc in proc_list:

            print('\t' + str(proc['proc_id']) + '\t' + proc['proc_name'])

    def __search_proc(self, proc_list, proc_id = None, proc_name = None):

        if proc_id:

            return [proc for proc in proc_list if proc['proc_id'] == proc_id]

        elif proc_name:

            return [proc for proc in proc_list if proc_name in proc['proc_name']]

        else:
            return None

    def do_chart(self, params, df):

        # find proc_id

        proc_list = self.__get_proc_list(df)

        if not params:

            self.__print_proc_list(proc_list)

            sys.exit('Please input process id or process name filter.')

        param = params[0]

        if param.isdigit():

            proc_id = int(param)

            results = self.__search_proc(proc_list, proc_id = proc_id)

            if not results:

                sys.exit('ERROR: Process not found.')

        else:

            results = self.__search_proc(proc_list, proc_name = param)

            if not results:

                sys.exit('ERROR: Process not found.')

            if len(results) > 1:

                self.__print_proc_list(results)

                sys.exit('Found multiple result, please specify process id or an unique process name.')

            proc_id = results[0]['proc_id']

        # plot chart

        self.plotter.plot(df[df.proc_id == proc_id], 'app cpu load', x='timestamp', y=[col for col in df.columns if 'cpu_load_' in col], kind='line', marker='.')