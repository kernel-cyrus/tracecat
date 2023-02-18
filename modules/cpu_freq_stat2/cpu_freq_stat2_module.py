import sys
import pandas

from framework.module import Module
from framework.helpers import create_duration_column

class Cpu_freq_stat2_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'cpu_freq_stat2'

    def get_desc(self):

        return 'CPU frequency statistics. (Based on cpu_freq2 module result.)'

    def get_help(self):

        text = '''
    统计cpu各频点运行时间占比（基于cpu_freq2）
    
    > tracecat "trace:cpu_freq2,cpu_freq_stat2"  # 抓取
    > tracecat "parse:cpu_freq2,cpu_freq_stat2"  # 解析
    > tracecat "chart:cpu_freq_stat2"            # 生成柱状图'''

        return text

    def invoke_sources(self):

        self.sysfs = self.invoke_source('sysfs', 'cpu_freq_table')

    def invoke_results(self):

        self.cpu_freq = self.invoke_result('cpu_freq2')

    def __get_cpu_list(self):

        cpu_list = list()

        for col in self.cpu_freq.columns:

            if 'cpu_freq_' in col:

                cpu_list.append(col.replace('cpu_freq_', ''))

        return sorted(cpu_list)

    def __get_cpu_freq(self, cpu_id):

        start_time, end_time = self.__get_trace_time()

        columns = dict()

        columns['cpu_freq_' + cpu_id] = 'cpu_freq'

        cpu_freq = self.cpu_freq.copy()

        cpu_freq = self.cpu_freq.rename(columns = columns)

        cpu_freq['timestamp'] = cpu_freq['timestamp']

        cpu_freq = create_duration_column(cpu_freq, end_time)

        return cpu_freq[['cpu_freq', 'duration']]

    def __get_trace_time(self):

        return self.cpu_freq.timestamp.min(), self.cpu_freq.timestamp.max()

    def do_parse(self, params):

        result = pandas.DataFrame()

        start_time, end_time = self.__get_trace_time()

        duration = end_time - start_time

        cpu_freq_table = self.sysfs.get_metrics('cpu_freq_table', None)

        for cpu_id in self.__get_cpu_list():

            cpu_freq = self.__get_cpu_freq(cpu_id)

            stats = cpu_freq.groupby(['cpu_freq']).sum().reset_index()

            # Add freq points

            if cpu_freq_table:

                for freq in cpu_freq_table[cpu_id]:

                    if stats[stats.cpu_freq == freq].empty:

                        stats = stats.append({'cpu_freq': freq, 'duration': 0}, ignore_index=True)

            # Add columns

            stats['cpu_id'] = cpu_id

            stats['percent'] = stats['duration'] / duration

            stats = stats.sort_values(by=['cpu_freq'])

            result = result.append(stats)

        result.reset_index(inplace=True)

        return result[['cpu_id', 'cpu_freq', 'percent']]

    def do_chart(self, params, df):

        if not params:

            sys.exit('ERROR: You need specify a cpu id.')

        if len(params) == 1:

            cpu_id = params[0]

            df = df[df.cpu_id == cpu_id]

            if df.empty:

                sys.exit('ERROR: cpu id not found.')

            self.plotter.plot(df, 'cpu%s' % cpu_id, x='cpu_freq', y='percent', kind='bar', color='orange')
