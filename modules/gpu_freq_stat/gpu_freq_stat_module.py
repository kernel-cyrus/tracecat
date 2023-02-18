from framework.module import Module
from framework.helpers import create_duration_column

class Gpu_freq_stat_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'gpu_freq_stat'

    def get_desc(self):

        return 'DDR frequency statistics. (Based on gpu_freq module result.)'

    def get_help(self):

        text = '''
    统计gpu各频点运行时间占比（基于gpu_freq）
    
    > tracecat "trace:gpu_freq,gpu_freq_stat"    # 抓取
    > tracecat "parse:gpu_freq,gpu_freq_stat"    # 解析
    > tracecat "chart:gpu_freq_stat"             # 生成柱状图'''

        return text

    def invoke_sources(self):

        self.sysfs = self.invoke_source('sysfs', 'gpu_freq_table')

    def invoke_results(self):

        self.gpu_freq = self.invoke_result('gpu_freq')

    def __get_gpu_freq(self):

        start_time, end_time = self.__get_trace_time()

        gpu_freq = self.gpu_freq.copy()

        gpu_freq = create_duration_column(gpu_freq, end_time)

        return gpu_freq[['gpu_freq', 'duration']]

    def __get_trace_time(self):

        return self.gpu_freq.timestamp.min(), self.gpu_freq.timestamp.max()

    def do_parse(self, params):

        start_time, end_time = self.__get_trace_time()

        duration = end_time - start_time

        gpu_freq = self.__get_gpu_freq()

        gpu_freq_table = self.sysfs.get_metrics('gpu_freq_table', None)

        stats = gpu_freq.groupby(['gpu_freq']).sum().reset_index()

        # Add freq points

        if gpu_freq_table:
            
            for freq in gpu_freq_table:

                if stats[stats.gpu_freq == freq].empty:

                    stats = stats.append({'gpu_freq': freq, 'duration': 0}, ignore_index=True)

        stats = stats.sort_values(by=['gpu_freq'])

        stats['percent'] = stats['duration'] / duration

        return stats[['gpu_freq', 'percent']]

    def do_chart(self, params, df):

        self.plotter.plot(df, x='gpu_freq', y='percent', kind='bar', color='orange')
