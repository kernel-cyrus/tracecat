import os
import sys
import pandas

from framework.module import Module
from framework.sources.profiler import Profiler

class Profiler_module(Module):

    def __init__(self):

        super().__init__()

        self.pickle_file = None

    def get_name(self):

        return 'profiler'

    def get_desc(self):

        return 'Qualcomm Snapdragon Profiler data'

    def get_help(self):

        text = '''
    半自动方式抓取、解析SnapdragonProfiler提供的所有数据
    (需要PC端安装高通Profiler工具)

    > tracecat "trace:profiler(cpu_branch_miss),profiler(cpu_cache_miss)"
      抓取cpu_branch_miss, cpu_cache_miss，开始后命令行会进入等待，请手动运行
      profiler，并在profiler中启动这些数据的抓取，然后在命令行按y继续。抓取结束
      后，命令行再次进入等待，请手动停止profiler，并将结果导出到./runs/xxx/prof
      iler/profiler.csv，然后按y继续。
    > tracecat "parse:profiler(cpu_branch_miss),profiler(cpu_cache_miss)"
      解析出cpu_branch_miss, cpu_cache_miss, cpu_clock
    > tracecat "chart:profiler(cpu_branch_miss)"
      显示cpu_branch_miss的图表

    当前支持的Metrics:
    ------------------------\n'''

        for metric, params in Profiler.metrics.items():

            text += '    ' + metric.ljust(24) + params['matcher'].replace('^', '').replace('$', '') + '\n'

        return text.rstrip()

    def invoke_sources(self):

        self.profiler = self.invoke_source('profiler')

    # Hijack module::save
    def save(self, pickle_file = None):

        return super().save(self.pickle_file)

    # Hijack module::export
    def export(self, excel_file = None):

        return super().export(self.excel_file)

    # Hijack module::load
    def load(self, pickle_file = None):

        if not pickle_file:

            self.results = pandas.DataFrame(['dummy'])

            return self.results

        return super().load(pickle_file)

    def do_parse(self, params):

        if not params:

            sys.exit('Please spicify a metrics for profiler module')

        metrics = params[0]

        self.pickle_file = self.workspace + self.get_name() + '_' + metrics + '.pkl'

        self.excel_file = self.workspace + self.get_name() + '_' + metrics + '.xlsx'

        results = self.profiler.get_metrics(metrics)

        return pandas.DataFrame(results)

    def do_chart(self, params, df):

        # load pickle file

        if not params:

            sys.exit('Please spicify a metrics for profiler module')

        metrics = params[0]

        pickle_file = self.workspace + self.get_name() + '_' + metrics + '.pkl'

        df = self.load(pickle_file)

        # draw chart

        if 'index' in df.columns:

            self.plotter.plot_index_chart(params[1:], df, metrics, index='index', x='timestamp', y=metrics, kind='line', marker='.')

        else:

            self.plotter.plot(df, metrics, x='timestamp', y=metrics, kind='line', marker='.')
