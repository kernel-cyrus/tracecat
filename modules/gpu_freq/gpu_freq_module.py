import pandas

from framework.module import Module
from framework.helpers import get_time

class Gpu_freq_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'gpu_freq'

    def get_desc(self):

        return 'GPU frequency. (Sample from sysfs)'

    def get_help(self):

        text = '''
    从sysfs采样GPU频率
    
    > tracecat "trace:gpu_freq"                  # 以500ms粒度采样（默认）
    > tracecat "trace:gpu_freq(100ms)"           # 以100ms粒度采样（模块设置）
    > tracecat "trace:gpu_freq" -s 100ms         # 以100ms粒度采样（全局设置）
    > tracecat "parse:gpu_freq"                  # 解析
    > tracecat "chart:gpu_freq"                  # 显示GPU频率曲线'''

        return text

    def invoke_sources(self):

        self.sysfs = self.invoke_source('sysfs', 'gpu_freq')

    def do_trace(self, params):

        period = get_time(params[0], 'ms') if params else None

        self.sysfs.config('gpu_freq', {'period': period})
        
    def do_parse(self, params):

        gpu_freqs = self.sysfs.get_metrics('gpu_freq')

        return pandas.DataFrame(gpu_freqs).rename(columns = {'time': 'timestamp', 'data': 'gpu_freq'})

    def do_chart(self, params, df):

        self.plotter.plot(df, 'gpu freq', x='timestamp', y='gpu_freq', kind='line', drawstyle='steps-post', marker='.')