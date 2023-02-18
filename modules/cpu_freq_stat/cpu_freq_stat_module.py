import sys
import pandas

from framework.module import Module
from framework.helpers import create_duration_column

class Cpu_freq_stat_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'cpu_freq_stat'

    def get_desc(self):

        return 'CPU frequency / idle state statistics. (Based on cpu_freq / cpu_idle module result.)'

    def get_help(self):

        text = '''
    统计cpu各频点及C-STATE运行时间占比（基于cpu_freq, cpu_idle）
    
    > tracecat "trace:cpu_freq,cpu_idle,cpu_freq_stat"      # 抓取
    > tracecat "parse:cpu_freq,cpu_idle,cpu_freq_stat"      # 解析
    > tracecat "chart:cpu_freq_stat"                        # 生成柱状图

    * 如果未抓取cpu_idle，则只解析频点的时间占比，不包含C-STATE信息'''

        return text

    def invoke_sources(self):

        self.sysfs = self.invoke_source('sysfs', 'cpu_freq_table')

    def invoke_results(self):

        self.cpu_freq = self.invoke_result('cpu_freq')

        self.cpu_idle = self.invoke_result('cpu_idle', return_when_fail = True)

    def __get_trace_time(self):

        return self.cpu_freq.timestamp.min(), self.cpu_freq.timestamp.max()

    def __get_cpu_list(self):

        return sorted(self.cpu_freq.cpu_id.unique())

    def __get_cpu_freq_subset(self):

        results = self.cpu_freq.copy()

        results['cpu_idle'] = None

        return results[['cpu_id', 'timestamp', 'cpu_freq', 'cpu_idle']]

    def __get_cpu_idle_subset(self):

        results = self.cpu_idle.copy()

        results['cpu_freq'] = None

        return results[['cpu_id', 'timestamp', 'cpu_freq', 'cpu_idle']]

    def do_parse(self, params):

        # Combine two dataset

        dataset = self.__get_cpu_freq_subset()

        if self.cpu_idle is not None:

            dataset = pandas.concat([dataset, self.__get_cpu_idle_subset()])

            dataset.sort_values(by=['cpu_id', 'timestamp'], inplace=True)

            dataset.fillna(method='ffill', inplace=True)

            dataset.dropna(inplace=True)

            dataset.reset_index(inplace=True)

        # Create duration column

        start_time, end_time = self.__get_trace_time()

        duration = end_time - start_time

        results = pandas.DataFrame()

        for cpu_id in self.__get_cpu_list():

            cpu_dataset = dataset[dataset.cpu_id == cpu_id].copy()

            results = results.append(create_duration_column(cpu_dataset, end_time=end_time))

        results = results[results['duration'] >= 0]

        results = results[['cpu_id', 'cpu_freq', 'cpu_idle', 'duration']]

        # Create statistics

        cpu_freq_table = self.sysfs.get_metrics('cpu_freq_table', None)

        stats = results.groupby(['cpu_id', 'cpu_freq', 'cpu_idle'], dropna=False).sum().reset_index()

        # Add missing freq points if we have freq table

        if cpu_freq_table:
            
            for cpu_id in self.__get_cpu_list():

                for freq in cpu_freq_table[str(cpu_id)]:

                    if stats[(stats.cpu_id == cpu_id) & (stats.cpu_freq == freq)].empty:

                        stats = stats.append({'cpu_id': cpu_id, 'cpu_freq': freq, 'cpu_idle': 0, 'duration': 0}, ignore_index=True)

        stats = stats.sort_values(by=['cpu_id', 'cpu_freq', 'cpu_idle']).reset_index()

        # Create percent column

        stats['percent'] = stats['duration'] / duration

        return stats[['cpu_id', 'cpu_freq', 'cpu_idle', 'duration', 'percent']]

    def do_chart(self, params, df):

        if not params:

            sys.exit('ERROR: You need specify a cpu id.')

        if len(params) == 1:

            cpu_id = int(params[0])

            df = df[df.cpu_id == cpu_id]

            if df.empty:

                sys.exit('ERROR: cpu id not found.')

            pivot_df = df.fillna('')

            pivot_df = pandas.pivot_table(data=pivot_df, index=['cpu_freq'], columns=['cpu_idle'], values=['percent'])

            pivot_df.columns.set_names(['percent', 'cpu_idle'], inplace=True)

            self.plotter.plot(pivot_df, 'cpu%s' % cpu_id, kind='bar', stacked=True)