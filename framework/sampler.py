# About sampler
# ------------------------------------------
# Sampler is for sampling from fs node or from command output. It support 
# sample for one time(info) or periodically(data) and stores all the results
# in a data file for loading it later, you can think it as a sampling data 
# database. It provides get_matrics api to get data from the data file.

import os
import sys
import time
import json
import threading

from framework.config import CONFIG
from framework.helpers import get_runtime_path, handle_thread_exceptions

EXEC_SEPERATOR = '___NeXt___'

class Sampler():

    counter = 0

    counter_mutex = threading.Lock()

    datafile_mutex = threading.Lock()

    def __init__(self, sampler_name = None):

        self.executor = None

        self.info_metrics = dict()

        self.data_metrics = dict()

        self.periods = set()

        self.data = dict()

        Sampler.counter_mutex.acquire()

        Sampler.counter += 1

        self.sampler_id = Sampler.counter

        Sampler.counter_mutex.release()

        self.sampler_name = sampler_name if sampler_name else sampler_id

    def init(self, executor):

        self.executor = executor

        if not self.executor.connect():

            return False

        return True

    def test_source(self, source, source_type):

        error_messages = [
            'No such file or directory',
            'Permission denied',
            'Operation not permitted',
            'Is a directory',
            'inaccessible or not found',
            'syntax error: unexpected'
        ]

        if type(source) == str:

            source = [source]

        if source_type == 'NODES':

            command = 'cat ' + ' '.join(source)
        else:
            command = '; '.join(source)

        result = self.executor.exec(command)

        for error in error_messages:

            if error in result:

                return False

        return True

    def register_metrics(self, metrics_name, source, parser = None, userdata = None, period = CONFIG['SAMPLING_PERIOD'], source_type = 'NODES', run_test = True):

        if source_type not in ['NODES', 'QUERY']:

            raise Exception('Invalid source type: %s' % source_type)

        if metrics_name in self.info_metrics or metrics_name in self.data_metrics:

            return False

        if type(source) == str:

            source = [source]

        if run_test and not self.test_source(source, source_type):

            return False

        metrics = self.data_metrics if period else self.info_metrics

        metrics[metrics_name] = {
            'name': metrics_name,
            'type': source_type,
            'source': source,
            'parser': parser,
            'period': period,
            'userdata': userdata
        }

        if period:

            self.periods.add(period)

        return True

    def __parse_data(self, metrics_name, raw_data):

        metrics = None

        results = None

        if metrics_name in self.info_metrics:

            metrics = self.info_metrics[metrics_name]

        elif metrics_name in self.data_metrics:

            metrics = self.data_metrics[metrics_name]

        if not metrics:

            raise Exception('Parsing invalid metrics: ' + metrics_name)

        if not metrics['parser']:

            return raw_data

        try:
            
            results = metrics['parser'](raw_data, metrics['userdata']) if metrics['userdata'] else metrics['parser'](raw_data)
        
        except:

            sys.exit('ERROR: Parse "%s" raw data failed: %s' % (metrics_name, raw_data))

        return results

    def __get_query_command(self, metrics_list):

        command = ''

        for metrics in metrics_list:

            if metrics['type'] == 'QUERY':

                inner_command = '; '.join(metrics['source'])

                command += 'echo "%s"; cat /proc/uptime | awk \'{print $1}\'; %s; echo "%s"; ' % (metrics['name'], inner_command, EXEC_SEPERATOR)

        return command

    def __parse_query_result(self, result):

        records = list()

        result = result.replace('\r', '')

        outputs = result.split(EXEC_SEPERATOR + '\n')

        for output in outputs:

            if not output:
                break

            parts = output.split('\n', 2)

            name = parts[0].strip()

            time = int(float(parts[1]) * 1000000000)

            data = self.__parse_data(metrics_name, parts[2])

            records.append({
                'metrics': name,
                'time': time,
                'data': data
            })

        return records

    def __get_nodes_command(self, metrics_list):

        command = ''

        for metrics in metrics_list:

            if metrics['type'] == 'NODES':

                command += (' "%s" ' % metrics['name']) + ' /proc/uptime ' + ' '.join(metrics['source']) + (' "%s" ' % EXEC_SEPERATOR)

        return 'cat' + command if command else command

    def __parse_nodes_result(self, result):

        records = list()

        result = result.replace('\r', '')

        outputs = result.split('cat: %s: No such file or directory' % EXEC_SEPERATOR + '\n')

        for output in outputs:

            if not output:
                break

            parts = output.split('\n', 2)

            name = parts[0].strip().replace(': No such file or directory', '')[5:]

            time = int(float(parts[1].split()[0]) * 1000000000)

            data = self.__parse_data(name, parts[2])

            records.append({
                'metrics': name,
                'time': time,
                'data': data
            })

        return records

    def __dump_metrics(self, metrics):

        results = dict()

        for name, item in metrics.items():

            results[name] = {
                'type': item['type'],
                'source': item['source'],
                'period': item['period']
            }

        return results

    def execute(self, metrics_list):

        nodes_command = self.__get_nodes_command(metrics_list)

        query_command = self.__get_query_command(metrics_list)

        if nodes_command:

            nodes_result = self.executor.exec(nodes_command)

        if query_command:

            query_result = self.executor.exec(query_command)

        records = list()

        if nodes_command and nodes_result.strip():

            records += self.__parse_nodes_result(nodes_result)

        if query_command and query_result.strip():

            records += self.__parse_query_result(query_result)

        return records

    def start(self, data_file, duration):

        # Write info results

        with open(data_file, 'w') as file:

            file.write('# INFO METRICS:\n')

            if self.info_metrics:

                file.write(json.dumps(self.__dump_metrics(self.info_metrics)) + '\n')

            file.write('# DATA METRICS:\n')

            if self.data_metrics:

                file.write(json.dumps(self.__dump_metrics(self.data_metrics)) + '\n')

            file.write('# INFO RESULTS:\n')

            records = self.execute(self.info_metrics.values())

            for record in records:

                file.write(json.dumps(record) + '\n')

            file.write('# DATA RESULTS:\n')

        # Select sampler mode

        sampling_mode = CONFIG['SAMPLING_MODE']

        if sampling_mode == 'ONLINE':

            sampling_func = self.__sampling_online

        elif sampling_mode == 'OFFLINE':

            sampling_func = self.__sampling_offline

            self.__clear_remote_folder()

        else:
            raise Exception('ERROR: Invalid sampling mode: %s' % sampling_mode)

        # Create sampler thread by period

        threads = list()

        for period in self.periods:

            metrics_list = [m for m in self.data_metrics.values() if m['period'] == period]

            thread = threading.Thread(target=sampling_func, args=(metrics_list, period, duration, data_file, ))

            threads.append({
                'name': '%s-%dms' % (self.sampler_name, period),
                'period': period,
                'thread': thread
            })

        for thread in threads:

            print('Start sampling thread: ' + thread['name'])

            thread['thread'].start()

        for thread in threads:

            thread['thread'].join()

            print('Thread finished: ' + thread['name'])

    @handle_thread_exceptions
    def __sampling_online(self, metrics_list, period, duration, data_file):

        with open(data_file, 'w') as file:

            run_time = 0

            end_time = time.time() + duration

            while run_time < end_time:

                run_time = time.time()

                records = self.execute(metrics_list)

                Sampler.datafile_mutex.acquire()

                for record in records:

                    file.write(json.dumps(record) + '\n')

                Sampler.datafile_mutex.release()

                sleep_time = period / 1000 - (time.time() - run_time)

                if sleep_time > 0:

                    time.sleep(sleep_time)

    @handle_thread_exceptions
    def __sampling_offline(self, metrics_list, period, duration, data_file):

        working_path = os.path.dirname(data_file)

        runtime_path = get_runtime_path()

        path = {
            'remote_proc': self.__get_remote_folder() + '/tracecatd-%s' % period,
            'remote_conf': self.__get_remote_folder() + '/tracecatd-%s.conf' % period,
            'remote_data': self.__get_remote_folder() + '/tracecatd-%s.data' % period,
            'local_proc': runtime_path + '/demon/obj/local/arm64-v8a/tracecatd',
            'local_conf': working_path + '/tracecatd-%s.conf' % period,
            'local_data': working_path + '/tracecatd-%s.data' % period,
        }

        # Push tracecatd to device

        if not os.path.exists(path['local_proc']):

            sys.exit('ERROR: Tracecatd not found.')

        self.executor.push(path['local_proc'], path['remote_proc'])

        self.executor.exec('chmod a+x %s' % path['remote_proc'])

        # Push tracecatd.conf to devcie

        config = self.__get_tracecatd_config(metrics_list)

        with open(path['local_conf'], 'w') as file:

            file.write(config)
        
        self.executor.push(path['local_conf'], path['remote_conf'])

        # Run tracecatd and wait for it finish

        ret = self.executor.exec('%s %s %s %s %s' % (path['remote_proc'], path['remote_conf'], path['remote_data'], period, duration, ))

        ret = ret.strip()

        if ret != 'Success!':

            sys.exit('ERROR: Tracecatd error: %s' % ret.strip())

        # Get tracecatd.data back

        self.executor.pull(path['remote_data'], path['local_data'])

        # Parse data from tracecat.data

        records = self.__parse_tracecatd_data(path['local_data'])

        Sampler.datafile_mutex.acquire()

        with open(data_file, 'a+') as file:
            
            for record in records:

                file.write(json.dumps(record) + '\n')

        Sampler.datafile_mutex.release()

    def __get_remote_folder(self):

        return CONFIG['REMOTE_ROOT'] + '/sampler-%s' % self.sampler_name

    def __clear_remote_folder(self):

        return self.executor.exec('rm -rf %s' % self.__get_remote_folder())

    def __get_tracecatd_config(self, metrics_list):

        config = ''

        for metrics in metrics_list:

            if metrics['type'] == 'NODES':

                config += 'NODES: %s\n' % metrics['name']

                for node in metrics['source']:

                    config += '    %s\n' % node

            elif metrics['type'] == 'QUERY':

                config += 'QUERY: %s\n' % metrics['name']

                for cmd in metrics['source']:

                    config += '    %s\n' % cmd

        return config

    def __parse_tracecatd_data(self, data_file):

        records = list()

        with open(data_file, 'r') as file:
            
            content = file.read()

            outputs = content.split(EXEC_SEPERATOR + '\n')

            for output in outputs:

                if not output:
                    break

                parts = output.split('\n', 2)

                name = parts[0][7:]

                time = int(parts[1])

                data = self.__parse_data(name, parts[2])

                records.append({
                    'metrics': name,
                    'time': time,
                    'data': data
                })

            return records  

    def load(self, data_file):

        # NOTE: Do not use self.info_metrics, self.data_metrics and self.excutor, this function shoud be able to use stand along.

        if not os.path.exists(data_file):

            return False

        parsing_results = False

        with open(data_file, 'r') as file:

            lines = file.readlines()

            for idx, line in enumerate(lines):

                if line[0] == '#':

                    if line == '# INFO RESULTS:\n' or line == '# DATA RESULTS:\n':

                        parsing_results = True

                    continue

                if parsing_results:

                    record = json.loads(line)

                    if record['metrics'] not in self.data:

                        self.data[record['metrics']] = list()

                    self.data[record['metrics']].append({
                        'time': record['time'],
                        'data': record['data'],
                    })

        return True

    def get_metrics(self, metrics_name, raise_exception = True):

        # NOTE: Do not use self.info_metrics, self.data_metrics and self.excutor, this function shoud be able to use stand along.

        if metrics_name not in self.data:

            if raise_exception:

                raise Exception('Metrics not found in data file: %s' % metrics_name)

            return None
            
        return self.data[metrics_name].copy()
