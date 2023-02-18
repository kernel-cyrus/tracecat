import pandas

from framework.module import Module

class Cpu_idle_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'cpu_idle'

    def get_desc(self):

        return 'CPU idle state (C-STATE) for each core. (Parse from trace)'

    def get_help(self):

        text = '''
    从perfetto的trace中解析CPU idle state (C-STATE)

    > tracecat "trace:cpu_idle"                  # 抓取perfetto trace
    > tracecat "parse:cpu_idle"                  # 解析cpu_idle
    > tracecat "chart:cpu_idle"                  # 显示所有cpu的idle state曲线
    > tracecat "chart:cpu_idle(0)"               # 显示cpu 0的idle state曲线'''

        return text

    def invoke_sources(self):

        self.perfetto = self.invoke_source('perfetto', 'cpu_idle')

    def __get_idle_points(self):

        return self.perfetto.query('select t.cpu cpu_id, c.ts timestamp, c.value as cpu_idle from counter as c left join cpu_counter_track as t on c.track_id = t.id where t.name = "cpuidle" order by t.cpu asc, c.ts asc')

    def do_parse(self, params):

        return pandas.DataFrame(self.__get_idle_points(), columns = ['cpu_id', 'timestamp', 'cpu_idle'])

    def do_chart(self, params, df):

        self.plotter.plot_index_chart(params, df, 'cpu idle', index='cpu_id', x='timestamp', y='cpu_idle', kind='line', drawstyle='steps-post', marker='.')