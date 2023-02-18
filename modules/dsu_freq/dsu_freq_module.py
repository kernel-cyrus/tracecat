import pandas

from framework.module import Module
from framework.helpers import create_seq_list, create_seq_dict

class Dsu_freq_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'dsu_freq'

    def get_desc(self):

        return 'CPU DSU frequency for each cluster. (Sample from sysfs)'

    def get_help(self):

        text = '''
    从sysfs采样DSU频率
    
    > tracecat "trace:dsu_freq"                  # 以500ms粒度采样（默认）
    > tracecat "trace:dsu_freq(100m)"            # 以100ms粒度采样（模块设置）
    > tracecat "trace:dsu_freq" -s 100ms         # 以100ms粒度采样（全局设置）
    > tracecat "parse:dsu_freq"                  # 解析
    > tracecat "chart:dsu_freq"                  # 显示DSU频率曲线'''

        return text

    def invoke_sources(self):

        self.sysfs = self.invoke_source('sysfs', 'dsu_freq')

    def do_trace(self, params):

        period = get_time(params[0], 'ms') if params else None

        self.sysfs.config('dsu_freq', {'period': period})
        
    def do_parse(self, params):

        results = list()

        dsu_freqs = self.sysfs.get_metrics('dsu_freq')

        for row in dsu_freqs:

            results.append({
                'timestamp': row['time'],
                'dsu_freq': max(row['data'].values())
            })

        return pandas.DataFrame(results)

    def do_chart(self, params, df):

        self.plotter.plot(df, 'dsu freq', x='timestamp', y='dsu_freq', kind='line', drawstyle='steps-post', marker='.')
