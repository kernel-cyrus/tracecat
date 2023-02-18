import pandas

from framework.module import Module
from framework.helpers import get_time

class Ddr_freq_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'ddr_freq'

    def get_desc(self):

        return 'DDR frequency. (Sample from sysfs)'

    def get_help(self):

        text = '''
    从sysfs采样DDR频率
    
    > tracecat "trace:ddr_freq"                  # 以500ms粒度采样（默认）
    > tracecat "trace:ddr_freq(100ms)"           # 以100ms粒度采样（模块设置）
    > tracecat "trace:ddr_freq" -s 100ms         # 以100ms粒度采样（全局设置）
    > tracecat "parse:ddr_freq"                  # 解析
    > tracecat "chart:ddr_freq"                  # 显示GPU频率曲线'''

        return text

    def invoke_sources(self):

        self.sysfs = self.invoke_source('sysfs', 'ddr_freq')

    def do_trace(self, params):

        period = get_time(params[0], 'ms') if params else None

        self.sysfs.config('ddr_freq', {'period': period})
        
    def do_parse(self, params):

        ddr_freqs = self.sysfs.get_metrics('ddr_freq')

        return pandas.DataFrame(ddr_freqs).rename(columns = {'time': 'timestamp', 'data': 'ddr_freq'})

    def do_chart(self, params, df):

        self.plotter.plot(df, 'ddr freq', x='timestamp', y='ddr_freq', kind='line', drawstyle='steps-post', marker='.')