import pandas

from framework.module import Module
from framework.helpers import get_slices, sub_slices, get_slices_usage, get_time, pick_next_window, create_seq_list, create_seq_dict

class Cpu_load_summary_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'cpu_load_summary'

    def get_desc(self):

        return 'CPU max / min / avg load for each core. (Calculate from cpu_load result)'

    def get_help(self):

        text = '''
    统计该场景cpu占用率的最大、最小、平均值
    
    > tracecat "trace:cpu_load"                  # 先要抓取cpu_load或者cpu_load2
    > tracecat "parse:cpu_load,cpu_load_summary" # 从cpu_load或cpu_load2的解析结果中计算统计结果
    > tracecat "chart:cpu_load_summary"          # 显示柱状图'''

        return text

    def invoke_results(self):

        self.cpu_load = self.invoke_result(['cpu_load', 'cpu_load2'])

    def do_parse(self, params):

        results = list()

        cpu_list = [x for x in self.cpu_load.columns if 'cpu_load_' in x]

        for cpu_id in cpu_list:

            results.append({
                'cpu_id': cpu_id.replace('cpu_load_', ''),
                'min_load': self.cpu_load[cpu_id].min(),
                'max_load': self.cpu_load[cpu_id].max(),
                'avg_load': self.cpu_load[cpu_id].mean(),
            })

        return pandas.DataFrame(results)

    def do_chart(self, params, df):

        self.plotter.plot(df, 'cpu load', kind='bar')
