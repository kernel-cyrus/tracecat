import sys
import pandas

from framework.module import Module
from framework.helpers import get_time

class Simpleperf_module(Module):

    def __init__(self):

        super().__init__()

    def get_name(self):

        return 'simpleperf'

    def get_desc(self):

        return 'Statistics simpleperf events.'

    def get_help(self):

        text = '''
    从simpleperf stat统计simpleperf events，支持全局采样和APP采样两种模式

    全局采样：
    > adb shell simpleperf list                                         # 获取手机支持的所有event
    > tracecat "trace:simpleperf(cache-misses,cpu-cycles)"              # 以500ms粒度全局采样（默认）
    > tracecat "trace:simpleperf(cache-misses,cpu-cycles|100ms)"        # 以100ms粒度全局采样
    * 全局采样包括各个cpu的单独统计数据

    APP采样：
    > adb shell pm list package                                         # 获取所有APP包名
    > tracecat "trace:simpleperf(com.android.dialer|cache-misses|100ms)"# 以100ms粒度只采样APP:com.android.dialer
    * APP采样只包括所有cpu的总和数据，不包括单独cpu的数据

    解析和显示：
    > tracecat "parse:simpleperf"                                       # 解析所有抓取的event
    > tracecat "parse:simpleperf(cache-misses,cpu-cycles)"              # 解析部分抓取的event
    > tracecat "chart:simpleperf"                                       # 显示所有event的曲线
    > tracecat "chart:simpleperf(cache-misses,cpu-cycles)"              # 显示部分event的曲线
    > tracecat "chart:simpleperf(cache-misses(cpu0),cpu-cycles(cpu0))"  # 显示某个核的event的曲线'''

        return text

    def invoke_sources(self):

        self.simpleperf = self.invoke_source('simpleperf')

    def __parse_params(self, params):

        app = None

        period = None

        events = params if params else None

        if events:

            mode = None

            if '|' in events[0] and len(events) == 1:

                parts = events[0].split('|')

                if len(parts) == 2:

                    mode = 'PERIOD' if parts[1][0].isdigit() else 'APP'

            if '|' in events[0] and mode != 'PERIOD':

                parts = events[0].split('|', 1)

                events[0] = parts[1].strip()

                app = parts[0]

            if '|' in events[-1] and mode != 'APP':

                parts = events[-1].rsplit('|', 1)

                events[-1] = parts[-2].strip()

                period = get_time(parts[-1].strip(), 'ms')

        return app, events, period

    def do_trace(self, params):

        app, events, period = self.__parse_params(params)

        if app:

            self.simpleperf.set_app(app)

        if events:

            self.simpleperf.enable(events)

        if period:

            self.simpleperf.set_period(period)
    
    def __check_complete(self, results):

        for col in results.values():

            if len(col) != len(results['timestamp']):

                sys.exit('ERROR: Simpleperf data broken, parse failed.')

    def __parse_global_format(self, df):

        results = {'timestamp': list()}

        prev_ts = 0

        for idx, row in df.iterrows():

            data = dict(row)

            if data['cpu'] is not None:

                sys.exit('ERROR: Simpleperf data broken, parse failed.')

            # Create event column

            event = data['event']

            if event not in results:

                results[event] = list()

            # Prev cycle should be complete if timestamp gap met.

            if row['timestamp'] - prev_ts > 10 * 1000000:

                self.__check_complete(results)

            prev_ts = data['timestamp']

            # Prev cycle should be complete if new row appended.

            if len(results[event]) == len(results['timestamp']):

                self.__check_complete(results)

                results['timestamp'].append(data['timestamp'])

            # Append new record

            results[event].append(data['count_normalize'])

        return pandas.DataFrame(results)

    def __parse_percpu_format(self, df):

        results = {'timestamp': list()}

        prev_ts = 0

        for idx, row in df.iterrows():

            data = dict(row)

            if data['cpu'] is None:

                sys.exit('ERROR: Simpleperf data broken, parse failed.')

            # Create event column

            event = data['event']

            if event not in results:

                results[event] = list()

            # Create event(cpu) column

            column = '%s(cpu%s)' % (data['event'], str(data['cpu']))

            if column not in results:

                results[column] = list()

            # Prev cycle should be complete if timestamp gap met.

            if row['timestamp'] - prev_ts > 10 * 1000000:

                self.__check_complete(results)

            prev_ts = data['timestamp']

            # Prev cycle should be complete if new row appended.

            if len(results[column]) == len(results['timestamp']):

                self.__check_complete(results)

                results['timestamp'].append(data['timestamp'])

            # Append new record

            results[column].append(data['count_normalize'])

            if len(results[event]) < len(results[column]):

                results[event].append(0)
            
            results[event][-1] += data['count_normalize']

        return pandas.DataFrame(results)

    def do_parse(self, params):

        dummy, events, dummy = self.__parse_params(params)

        df = self.simpleperf.get_data(event = events)

        if not df.empty and df['cpu'].iloc[0] is None:

            return self.__parse_global_format(df)

        else:

            return self.__parse_percpu_format(df)

    def do_chart(self, params, df):

        dummy, events, dummy = self.__parse_params(params)

        columns = df.columns

        if events:

            columns = ['timestamp']

            for col in df.columns:

                for event in events:

                    if col.startswith(event):

                        columns.append(col)

        self.plotter.plot(df[columns], 'simpleperf events', x='timestamp', kind='line', marker='.')
