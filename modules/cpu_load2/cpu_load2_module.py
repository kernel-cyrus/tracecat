import pandas

from framework.module import Module
from framework.helpers import create_seq_list, create_seq_dict, get_time

class Cpu_load2_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'cpu_load2'

    def get_desc(self):

        return 'CPU load for each core. (Sample from procfs)'

    def get_help(self):

        text = '''
    从procfs采样CPU占用率
    
    > tracecat "trace:cpu_load2"                 # 以500ms粒度采样（默认）
    > tracecat "trace:cpu_load2(100ms)"          # 以100ms粒度采样（模块设置）
    > tracecat "trace:cpu_load2" -s 100ms        # 以100ms粒度采样（全局设置）
    > tracecat "parse:cpu_load2"                 # 解析
    > tracecat "chart:cpu_load2"                 # 显示各cpu占用率
    > tracecat "chart:cpu_load2(0)"              # 只显示cpu 0的占用率
    > tracecat "chart:cpu_load2(0-4,5-6,7)"      # 显示平均占用率'''

        return text

    def invoke_sources(self):

        self.procfs = self.invoke_source('procfs', 'stat')

    def do_trace(self, params):

        period = get_time(params[0], 'ms') if params else None

        self.procfs.config('stat', {'period': period})

    def do_parse(self, params):

        stats = self.procfs.get_metrics('stat')

        cpu_ids = sorted(stats[0]['data']['cpu'].keys()) if stats else []

        columns = create_seq_list('timestamp', 'cpu_load_', cpu_ids)

        results = create_seq_dict('timestamp', 'cpu_load_', cpu_ids, list)

        prev_row = None

        for row in stats:

            if prev_row:

                record = dict()

                complete_recored = True

                for cpu_id, this_stat in row['data']['cpu'].items():

                    column = 'cpu_load_' + str(cpu_id)

                    prev_stat = prev_row['data']['cpu'][cpu_id]

                    prev_time = sum(prev_stat.values())

                    this_time = sum(this_stat.values())

                    if this_time - prev_time == 0:

                        complete_recored = False

                        break

                    cpu_load = ((this_time - this_stat['idle']) - (prev_time - prev_stat['idle'])) / (this_time - prev_time) * 100

                    record[column] = cpu_load

                if complete_recored:

                    results['timestamp'].append(row['time'])

                    for column, cpu_load in record.items():

                        results[column].append(cpu_load)

                    prev_row = row.copy()
            else:
                prev_row = row.copy()

        return pandas.DataFrame(results, columns = columns)

    def do_chart(self, params, df):

        self.plotter.plot_paral_chart(params, df, 'cpu load', x='timestamp', y_prefixer='cpu_load_', kind='line', marker='.')
