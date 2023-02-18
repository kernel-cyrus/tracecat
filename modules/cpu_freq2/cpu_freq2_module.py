import pandas

from framework.module import Module
from framework.helpers import create_seq_list, create_seq_dict, get_time

class Cpu_freq2_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'cpu_freq2'

    def get_desc(self):

        return 'CPU frequency for each core. (Sample from sysfs)'

    def get_help(self):

        text = '''
    从sysfs采样CPU频率
    
    > tracecat "trace:cpu_freq2"                 # 以500ms粒度采样（默认）
    > tracecat "trace:cpu_freq2(100ms)"          # 以100ms粒度采样（模块设置）
    > tracecat "trace:cpu_freq2" -s 100ms        # 以100ms粒度采样（全局设置）
    > tracecat "parse:cpu_freq2"                 # 解析
    > tracecat "chart:cpu_freq2"                 # 显示所有cpu的频率曲线
    > tracecat "chart:cpu_freq2(0)"              # 只显示cpu 0的频率曲线
    > tracecat "chart:cpu_freq2(0,4,7)"          # 显示cpu0,4,7的频率曲线(cluster)'''

        return text

    def invoke_sources(self):

        self.sysfs = self.invoke_source('sysfs', 'cpu_freq')

    def do_trace(self, params):

        period = get_time(params[0], 'ms') if params else None

        self.sysfs.config('cpu_freq', {'period': period})
        
    def do_parse(self, params):

        cpu_freqs = self.sysfs.get_metrics('cpu_freq')

        cpu_ids = sorted(cpu_freqs[0]['data'].keys()) if cpu_freqs else []

        columns = create_seq_list('timestamp', 'cpu_freq_', cpu_ids)

        results = create_seq_dict('timestamp', 'cpu_freq_', cpu_ids, list)

        for row in cpu_freqs:

            results['timestamp'].append(row['time'])

            for cpu_id, cpu_freq in row['data'].items():

                column = 'cpu_freq_' + str(cpu_id)

                results[column].append(cpu_freq)

        return pandas.DataFrame(results, columns = columns)

    def do_chart(self, params, df):

        self.plotter.plot_paral_chart(params, df, 'cpu freq', x='timestamp', y_prefixer='cpu_freq_', kind='line', drawstyle='steps-post', marker='.')
