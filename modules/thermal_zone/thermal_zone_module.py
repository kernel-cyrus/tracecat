import pandas

from framework.module import Module
from framework.helpers import create_seq_list, create_seq_dict, get_time

class Thermal_zone_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'thermal_zone'

    def get_desc(self):

        return 'Thermal zone temperature. (Sample from sysfs)'

    def get_help(self):

        text = '''
    从sysfs采样thermal信息

    > tracecat "trace:thermal_zone"              # 以500ms粒度采样所有thermal节点（默认）
    > tracecat "trace:thermal_zone(0,1,2)" -s 1s # 以1s粒度采样0,1,2三个zone（设置全局采样频率为1s）
    > tracecat "trace:thermal_zone(0,1,2|1s)"    # 以1s粒度采样0,1,2三个zone（设置模块采样频率为1s）
    > tracecat "parse:thermal_zone"              # 解析
    > tracecat "chart:thermal_zone"              # 显示所有thermal曲线
    > tracecat "chart:thermal_zone(0,1,2)"       # 显示0,1,2三个zone曲线

    * 由于大部分手机thermal节点比较多，建议尽量降低采样频率（>500ms）'''

        return text

    def invoke_sources(self):

        self.sysfs = self.invoke_source('sysfs', 'thermal_zone')

    def __parse_params(self, params):

        period = None

        zone_ids = params if params else None

        if zone_ids:

            if '|' in zone_ids[-1]:

                parts = zone_ids[-1].split('|')

                zone_ids[-1] = parts[0].strip()

                period = get_time(parts[1].strip(), 'ms')

            elif len(zone_ids) == 1 and zone_ids[0][-1] == 's':
                
                period = get_time(zone_ids[0].strip(), 'ms')

                zone_ids = None

        return zone_ids, period

    def do_trace(self, params):

        zone_ids, period = self.__parse_params(params)

        self.sysfs.config('thermal_zone', {'filter': zone_ids, 'period': period})

    def do_parse(self, params):

        zones = self.sysfs.get_metrics('thermal_zone')

        zone_ids = sorted(zones[0]['data'].keys()) if zones else []

        columns = create_seq_list('timestamp', 'thermal_zone_', zone_ids)

        results = create_seq_dict('timestamp', 'thermal_zone_', zone_ids, list)

        for row in zones:

            results['timestamp'].append(row['time'])

            for zone_id, temperature in row['data'].items():

                column = 'thermal_zone_' + str(zone_id)

                results[column].append(temperature)

        return pandas.DataFrame(results, columns = columns)

    def do_chart(self, params, df):

        self.plotter.plot_paral_chart(params, df, 'thermal zone', x='timestamp', y_prefixer='thermal_zone_', kind='line', marker='.')
