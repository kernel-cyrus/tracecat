from framework.module import Module
from framework.helpers import create_duration_column

class Ddr_freq_stat_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'ddr_freq_stat'

    def get_desc(self):

        return 'DDR frequency statistics. (Based on ddr_freq module result.)'

    def get_help(self):

        text = '''
    统计ddr各频点运行时间占比（基于ddr_freq）
    
    > tracecat "trace:ddr_freq,ddr_freq_stat"    # 抓取
    > tracecat "parse:ddr_freq,ddr_freq_stat"    # 解析
    > tracecat "chart:ddr_freq_stat"             # 生成柱状图'''

        return text

    def invoke_sources(self):

        self.sysfs = self.invoke_source('sysfs', 'ddr_freq_table')

    def invoke_results(self):

        self.ddr_freq = self.invoke_result('ddr_freq')

    def __get_ddr_freq(self):

        start_time, end_time = self.__get_trace_time()

        ddr_freq = self.ddr_freq.copy()

        ddr_freq = create_duration_column(ddr_freq, end_time)

        return ddr_freq[['ddr_freq', 'duration']]

    def __get_trace_time(self):

        return self.ddr_freq.timestamp.min(), self.ddr_freq.timestamp.max()

    def do_parse(self, params):

        start_time, end_time = self.__get_trace_time()

        duration = end_time - start_time

        ddr_freq = self.__get_ddr_freq()

        ddr_freq_table = self.sysfs.get_metrics('ddr_freq_table', None)

        stats = ddr_freq.groupby(['ddr_freq']).sum().reset_index()

        # Add freq points

        if ddr_freq_table:
            
            for freq in ddr_freq_table:

                if stats[stats.ddr_freq == freq].empty:

                    stats = stats.append({'ddr_freq': freq, 'duration': 0}, ignore_index=True)

        stats = stats.sort_values(by=['ddr_freq'])

        stats['percent'] = stats['duration'] / duration

        return stats[['ddr_freq', 'percent']]

    def do_chart(self, params, df):

        self.plotter.plot(df, x='ddr_freq', y='percent', kind='bar', color='orange')
    