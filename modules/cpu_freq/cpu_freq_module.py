import pandas

from framework.module import Module

class Cpu_freq_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'cpu_freq'

    def get_desc(self):

        return 'CPU frequency for each core. (Parse from trace)'

    def get_help(self):

        text = '''
    从perfetto的trace中解析CPU频率

    > tracecat "trace:cpu_freq"                  # 抓取perfetto trace
    > tracecat "parse:cpu_freq"                  # 解析cpu_freq
    > tracecat "chart:cpu_freq"                  # 显示所有cpu的频率曲线
    > tracecat "chart:cpu_freq(0)"               # 只显示cpu 0的频率曲线
    > tracecat "chart:cpu_freq(0,4,7)"           # 显示cpu0,4,7的频率曲线(cluster)'''

        return text

    def invoke_sources(self):

        self.perfetto = self.invoke_source('perfetto', 'cpu_freq')

    def __get_freq_points(self):

        return self.perfetto.query('select t.cpu cpu_id, c.ts timestamp, c.value as cpu_freq from counter as c left join cpu_counter_track as t on c.track_id = t.id where t.name = "cpufreq" order by t.cpu asc, c.ts asc')

    def do_parse(self, params):

        return pandas.DataFrame(self.__get_freq_points(), columns = ['cpu_id', 'timestamp', 'cpu_freq'])

    def do_chart(self, params, df):

        self.plotter.plot_index_chart(params, df, 'cpu freq', index='cpu_id', x='timestamp', y='cpu_freq', kind='line', drawstyle='steps-post', marker='.')