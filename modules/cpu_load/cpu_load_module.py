import pandas

from framework.module import Module
from framework.helpers import get_slices, sub_slices, get_slices_usage, get_time, pick_next_window, create_seq_list, create_seq_dict

class Cpu_load_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'cpu_load'

    def get_desc(self):

        return 'CPU load for each core. (Parse from trace)'

    def get_help(self):

        text = '''
    从perfetto的trace中解析CPU占用率

    > tracecat "trace:cpu_load"                 # 抓取perfetto trace
    > tracecat "parse:cpu_load"                 # 以1s粒度解析占用率
    > tracecat "parse:cpu_load(100ms)"          # 以100ms粒度解析占用率
    > tracecat "chart:cpu_load"                 # 显示各cpu占用率
    > tracecat "chart:cpu_load(0)"              # 只显示cpu 0的占用率
    > tracecat "chart:cpu_load(0-4,5-6,7)"      # 显示平均占用率
    
    * 不建议长时间抓取，因为生成的trace文件可能过大，长时间抓取请使用cpu_load2'''

        return text

    def invoke_sources(self):

        self.perfetto = self.invoke_source('perfetto', 'sched')

    def __get_sched_slices(self, cpu_id):

        results = self.perfetto.query('select ts start_time, ts_end end_time, dur duration from sched where cpu = %s and utid > 0 order by ts asc' % cpu_id)

        return get_slices(results, 'start_time', 'end_time', 'duration')

    def do_parse(self, params):

        window = None

        window_time = get_time(params[0], 'ms') * 1000000 if params else 1000 * 1000000

        trace_info = self.perfetto.get_trace_info()

        cpu_ids = trace_info['cpu_list']

        columns = create_seq_list('timestamp', 'cpu_load_', cpu_ids)

        results = create_seq_dict('timestamp', 'cpu_load_', cpu_ids, list)

        for cpu_id in cpu_ids:

            column = 'cpu_load_' + str(cpu_id)

            sched_slices = self.__get_sched_slices(cpu_id)

            while window := pick_next_window(window, trace_info['start_time'], trace_info['end_time'], window_time, True):

                window_slices = sub_slices(sched_slices, window['start'], window['end'])

                cpu_load = get_slices_usage(window_slices, window['start'], window['end'])

                results[column].append(int(cpu_load * 10000) / 100)

                if len(results['timestamp']) == window['id']: # only append in first loop

                    results['timestamp'].append(window['end'])
                    
        return pandas.DataFrame(results, columns = columns)

    def do_chart(self, params, df):

        self.plotter.plot_paral_chart(params, df, 'cpu load', x='timestamp', y_prefixer='cpu_load_', kind='line', marker='.')
