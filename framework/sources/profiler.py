import os
import sys
import time
import click
import json
import pandas

from framework.source import Source
from framework.executors.adb_executor import Adb_executor

class Profiler(Source):

    # Register new metrics here.
    
    metrics = {
        # CPU
        'cpu_branch_miss':      {'matcher': '^CPU ([0-9]*) Branch Misses$',         'indexer': True},
        'cpu_cache_miss':       {'matcher': '^CPU ([0-9]*) Cache Misses$',          'indexer': True},
        'cpu_cache_miss_r':     {'matcher': '^CPU ([0-9]*) Cache Miss Ratio$',      'indexer': True},
        'cpu_cache_refs':       {'matcher': '^CPU ([0-9]*) Cache Refs$',            'indexer': True},
        'cpu_clock':            {'matcher': '^CPU ([0-9]*) Clock$',                 'indexer': True},
        'cpu_cs':               {'matcher': '^CPU ([0-9]*) Context Switches$',      'indexer': True},
        'cpu_freq':             {'matcher': '^CPU ([0-9]*) Frequency$',             'indexer': True},
        'cpu_load':             {'matcher': '^CPU ([0-9]*) Load$',                  'indexer': True},
        'cpu_util':             {'matcher': '^CPU ([0-9]*) % Utilization$',         'indexer': True},
        'cpu_cycles':           {'matcher': '^CPU ([0-9]*) Cycles$',                'indexer': True},
        'cpu_inst':             {'matcher': '^CPU ([0-9]*) Instructions$',          'indexer': True},
        'cpu_page_faults':      {'matcher': '^CPU ([0-9]*) Page Faults$',           'indexer': True},
        # GPU
        'gpu_clock_per_sec':    {'matcher': '^Clocks / Second$'},
        'gpu_bus_busy':         {'matcher': '^GPU % Bus Busy$'},
        'gpu_util':             {'matcher': '^GPU % Utilization$'},
        'gpu_freq':             {'matcher': '^GPU Frequency$'},
        'gpu_temp':             {'matcher': '^GPU Temperature$'},
        'gpu_bytes_per_frag':   {'matcher': '^Avg Bytes / Fragment$'},
        'gpu_bytes_per_vert':   {'matcher': '^Avg Bytes / Vertex$'},
        'gpu_total_read':       {'matcher': '^Read Total (Bytes/sec)$'},
        'gpu_sp_mem_read':      {'matcher': '^SP Memory Read (Bytes/Second)$'},
        'gpu_texture_mem_read': {'matcher': '^Texture Memory Read BW (Bytes/Second)$'},
        'gpu_vertex_mem_read':  {'matcher': '^Vertex Memory Read (Bytes/Second)$'},
        'gpu_total_write':      {'matcher': '^Write Total (Bytes/sec)$'},        
    }

    def __init__(self):

        super().__init__()

        self.trace_info = {
            'boot_time': None,
            'start_time': None,
            'end_time': None
        }

        self.data = None

        self.info = None

    def init_workspace(self, workspace):

        super().init_workspace(workspace)

        self.data_file = self.get_workspace() + 'profiler.csv'

        self.info_file = self.get_workspace() + 'trace_info.json'

    def __get_config(self, duration):

        return None

    def _name(self):

        return 'profiler'

    def _enable(self, item):

        pass

    def _trace(self, duration):

        time.sleep(duration)

    def _pre_trace(self, duration):

        # Run snapdragon profiler mannully.

        print('Please open snapdragon profiler and start realtime tracing...')

        confirm = click.confirm('Continue: Is the tracing started?', default=True)

        if not confirm:

            sys.exit('ERROR: Profiler data source canceled.')

        # Get start time.

        executor = Adb_executor()

        if not executor.connect():

            sys.exit('ERROR: Adb device not found.')

        results = executor.exec('cat /proc/uptime | awk \'{print $1}\'; date +%s.%N')

        data = results.split()

        self.trace_info['start_time'] = int(float(data[1]) * 1000000) # us

        self.trace_info['boot_time'] = self.trace_info['start_time'] - int(float(data[0]) * 1000000) # us

        self.trace_info['end_time'] = self.trace_info['start_time'] + duration * 1000000

    def _post_trace(self, duration):

        # Get end time.

        executor = Adb_executor()

        if not executor.connect():

            sys.exit('ERROR: Adb device not found.')

        # Stop snapdragon profiler mannully.

        confirm = True

        while (confirm):

            print('Please stop snapdragon profiler and export the data file to the following path:')

            print(os.path.abspath(self.data_file))

            confirm = click.confirm('Continue: Is the file exported?', default=True)

            if confirm:

                # Check data file is there.

                if os.path.exists(self.data_file):

                    # Create info file.

                    with open(self.info_file, 'w') as file:

                        json.dump(self.trace_info, file)

                    break

                else:
                    print('WARNING: File not found, please check export path.')

            else:
                print('WARNING: Profiler data source canceled.')

    def _parse(self):
        
        # Load data & info file.

        self.data = pandas.read_csv(self.data_file)

        with open(self.info_file, 'r') as file:

            self.info = json.load(file)

        # Only keep the data between start_time and end_time

        self.data.drop(columns=['Timestamp'], inplace=True)

        self.data.rename(columns = {'Process': 'process', 'Metric': 'metric', 'TimestampRaw': 'timestamp', 'Value': 'value'}, inplace=True)

        self.data = self.data[(self.data.timestamp >= self.info['start_time']) & (self.data.timestamp <= self.info['end_time'])]

        self.data.timestamp = (self.data.timestamp - self.info['boot_time']) * 1000

    def get_raw_metric(self, raw_metric):

        return self.data[self.data.metric==raw_metric].to_dict(orient='records')

    def get_metrics(self, metrics_name, raise_exception = True):

        # Check metrics is valid.

        if self.data is None:

            raise Exception('Metrics data used before loaded.')

        if metrics_name not in self.metrics:

            if raise_exception:

                raise Exception('Metrics not supported: %s' % metrics_name)

            return None
        
        # Generate results

        matcher = self.metrics[metrics_name]['matcher']

        dataset = self.data[self.data.metric.str.match(matcher)]

        results = pandas.DataFrame()

        if 'indexer' in self.metrics[metrics_name]:

            indexer = self.metrics[metrics_name]['indexer']

            if indexer is True:

                indexer = matcher
                
            if indexer is not None:

                results['index'] = dataset.metric.str.extract(indexer, expand = False)

        results['timestamp'] = dataset.timestamp

        results[metrics_name] = dataset.value

        results.reset_index(drop=True, inplace=True)

        return results
