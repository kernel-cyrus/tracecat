# About basefs
# ------------------------------------------
# Basefs is a file node sampler's base class. It provides a file node sampler
# template so that the specific file system sampler can just implement a node
# list(metrics function) and all the magic will take effect. Basefs will get
# all the metrics (implemented by the child class) and register them into
# sampler, and tell the sampler whitch are the info nodes and witch are data
# nodes, and let the sampler do the rest of the work. Finally it provides
# get_metrics function for the modules which will get the data from sampler's
# database file.

import os
import sys
import re

from abc import ABC, abstractmethod

from framework.source import Source
from framework.sampler import Sampler
from framework.executors.adb_executor import Adb_executor
from framework.config import CONFIG

class Basefs(Source, ABC):

    def __init__(self):

        super().__init__()

        self.sampler = Sampler(self.name())

        self.metrics = self.metrics()

        self.enabled = set()

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def metrics(self):  
        pass
        
    def _name(self):
        
        return self.name()

    def _enable(self, item):

        if item not in self.metrics:

            raise Exception('Metrics not supported: %s' % item)

        if item not in self.enabled:

            self.enabled.add(item)

    def _config(self, item, conf):

        if item not in self.enabled:

            raise Exception('Metrics configure before enabled: %s' % item)

        if 'period' in conf:

            self.metrics[item]['period'] = conf['period']

        if 'filter' in conf:

            self.metrics[item]['filter'] = conf['filter']

    def _trace(self, duration):

        executor = Adb_executor()

        ret = self.sampler.init(Adb_executor())

        if not ret or not executor.connect():

            sys.exit('ERROR: Adb device connect failed.')

        # Regist metrics profile.

        for metrics_name in self.enabled:

            is_registed = False

            metrics_type = self.metrics[metrics_name]['type']

            period = None

            if metrics_type == 'DATA':

                period = self.metrics[metrics_name].get('period', None)

                if period is None:

                    period = CONFIG['SAMPLING_PERIOD']

            for profile in self.metrics[metrics_name]['profiles']: # Find a suitble node to register

                if self.sampler.test_source(profile['nodes'], source_type = 'NODES'):

                    nodelist = profile['nodes']

                    userdata = ''

                    # Parse batch nodes

                    if type(profile['nodes']) == str and ('*' in profile['nodes'] or '?' in profile['nodes']):

                        results = executor.exec('ls -l %s | awk \'{print $NF}\'' % profile['nodes']).split('\n')

                        results = [x for x in results if x]

                        pattern = re.split('\*|\?', profile['nodes'])

                        for row in results:

                            node_id = row[len(pattern[0]):-len(pattern[-1])]

                            userdata += node_id + '\n'

                        if CONFIG['SAMPLING_MODE'] == 'OFFLINE':

                            id_filter = self.metrics[metrics_name].get('filter', list())

                            if id_filter:

                                nodelist = list()

                                userdata = ''

                                for row in results:

                                    node_id = row[len(pattern[0]):-len(pattern[-1])]

                                    if str(node_id) in id_filter:

                                        nodelist.append(row)

                                        userdata += node_id + '\n'
                            else:

                                nodelist = results

                    is_registed = self.sampler.register_metrics(metrics_name, nodelist, profile['parser'], userdata = userdata if userdata else None, period = period, source_type = 'NODES', run_test = False)

                    if is_registed:

                        break

            if not is_registed:

                print('WARNING: Can\'t enable metrics on device: %s' % metrics_name)

        # Start sampling.

        print('Start sampling: %s...' % self.name())

        data_file = self.get_workspace() + '%s.data' % self.get_name()

        self.sampler.start(data_file, duration)

        print('Done. (%s)' % data_file)

    def _parse(self):

        data_file = self.get_workspace() + '%s.data' % self.get_name()

        if not os.path.exists(data_file):

            sys.exit('ERROR: %s data file not found: ' % self.get_name() + data_file)

        ret = self.sampler.load(data_file)

        if not ret:

            sys.exit('ERROR: can not load %s data file.' % self.get_name() + data_file)

    def get_metrics(self, metrics_name, not_found_value = 'EXCEPTION'):

        if metrics_name not in self.metrics:

            raise Exception('Metrics not supported: %s' % metrics_name)

        result = self.sampler.get_metrics(metrics_name, raise_exception = (not_found_value == 'EXCEPTION'))

        if result is None:

            return None

        metrics_type = self.metrics[metrics_name]['type']

        return result if metrics_type == 'DATA' else result[0]['data']

    def batch_nodes_parser(self, outputs, userdata = None, parser = None):

        results = dict()

        vals = outputs.split('\n')

        keys = userdata.split('\n')

        for idx, val in enumerate(vals):

            if keys[idx]:

                results[keys[idx]] = parser(val) if parser else val

        return results