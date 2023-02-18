import sys
import pandas

from framework.module import Module

#FIXME: freq, idle dur config for different device
#FIXME: auto find profiler thread id
#FIXME: select run mode

class Ios_cpu_freq_module(Module):

    def __init__(self):

        super().__init__()

        # this config is for iPhone12

        self.sm_max_freq = 1823
        self.lg_max_freq = 2998

        self.sm_idle_dur = [166, 167, 208, 209, 250, 291, 292, 333, 334, 375, 416, 417, 458, 459, 500, 541, 542, 583, 584]
        self.lg_idle_dur = []

    def get_desc(self):

        return 'CPU frequency for each core, for iPhone. (Hack from trace)'

    def get_name(self):

        return 'ios_cpu_freq'

    def get_help(self):

        text = '''
    iPhone CPU频率（Hack方式，实验功能）
    
    * 不建议使用'''

        return text

    def invoke_sources(self):

        self.instruments = self.invoke_source('instruments')

    def __get_cpu_state(self):

        return self.instruments.get_cpu_state().to_dict(orient='records')

    def __get_thread_data(self, thread_id):

        df_cpu_state = self.instruments.get_cpu_state()

        return df_cpu_state.loc[df_cpu_state.thread_id == thread_id].to_dict(orient='records')

    def do_parse(self, params):

        return self.idlehack_mode()

    def do_chart(self, params, df):

        self.plotter.plot(df[df.cpu_id <= 3], 'cpu freq', x='timestamp', y='cpu_freq', label='cpu_freq_sm', drawstyle='steps-post', marker='.')

    def idlehack_mode(self):

        results = list()

        matching = dict()

        cpu_state = self.__get_cpu_state()

        for row in cpu_state:

            if row['cpu_state'] == 'Handling Interrupt':

                matching[row['cpu_id']] = True

            elif row['cpu_id'] in matching and matching[row['cpu_id']] and row['cpu_state'] == 'Running' and row['process_id'] == '0' and row['priority'] == 0:
                
                if row['cpu_id'] in [0, 1, 2, 3] and row['duration'] in self.sm_idle_dur:

                    results.append({
                        'cpu_id':    row['cpu_id'],
                        'timestamp': row['start_time'],
                        'cpu_freq':  int(167 / row['duration'] * self.sm_max_freq)
                    })

                elif row['cpu_id'] in [4, 5] and row['duration'] in self.lg_idle_dur:
                
                    results.append({
                        'cpu_id':    row['cpu_id'],
                        'timestamp': row['start_time'],
                        'cpu_freq':  int(0 / row['duration'] * self.lg_max_freq)
                    })

                else:
                    matching[row['cpu_id']] = False

            else:
                matching[row['cpu_id']] = False
        
        return pandas.DataFrame(results, columns = ['cpu_id', 'timestamp', 'cpu_freq'])

    def profiler_mode(self):

        results = list()

        cpu_state = self.__get_cpu_state()

        # find profiler tid

        thread_id = '0x2026f2' # FIXME: find a way to get profiler tid

        thread_data = self.__get_thread_data(thread_id)

        if not thread_data:

            sys.exit('Profiler thread not found.')

        # Get running time

        min_sm_time = 0
        max_sm_time = 0
        min_lg_time = 0
        max_lg_time = 0

        run = {
            'start_time': thread_data[0]['start_time'],
            'end_time': thread_data[0]['end_time'],
            'duration': 0,
            'clusters': []
        }

        gap_time = 8 * 1000 * 1000

        for data in thread_data:

            cluster = 'sm' if data['cpu_id'] in [0, 1, 2, 3] else 'lg'

            # Append new run
            if data['start_time'] > run['end_time'] + gap_time:

                record = {
                    'timestamp': run['end_time'],
                    'sm_time': run['duration'] if 'lg' not in run['clusters'] else 0,
                    'lg_time': run['duration'] if 'sm' not in run['clusters'] else 0
                }

                min_sm_time = record['sm_time'] if record['sm_time'] and (not min_sm_time or record['sm_time'] < min_sm_time) else min_sm_time
                max_sm_time = record['sm_time'] if record['sm_time'] and (not max_sm_time or record['sm_time'] > max_sm_time) else max_sm_time
                min_lg_time = record['lg_time'] if record['lg_time'] and (not min_lg_time or record['lg_time'] < min_lg_time) else min_lg_time
                max_lg_time = record['lg_time'] if record['lg_time'] and (not max_lg_time or record['lg_time'] > max_lg_time) else max_lg_time

                results.append(record)

                run['start_time'] = data['start_time']
                run['end_time']   = data['end_time']
                run['duration']   = data['duration']
                run['clusters']   = [cluster]

            # Run is going
            else:
                run['end_time']  = data['end_time']
                run['duration'] += data['duration']
                run['clusters'].append(cluster)

        # Write freq data

        for record in results:

            record['sm_freq'] = int(self.sm_max_freq * min_sm_time / record['sm_time']) if record['sm_time'] else 0
            record['lg_freq'] = int(self.lg_max_freq * min_lg_time / record['lg_time']) if record['lg_time'] else 0

        return pandas.DataFrame(results, columns=['timestamp', 'sm_time', 'lg_time', 'sm_freq', 'lg_freq'])
