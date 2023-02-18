import os
import sys
import pandas
import platform
import xml.etree.ElementTree as xml

from framework.source import Source
from framework.helpers import get_unique_list, get_runtime_path

#FIXME: auto select device

class Instruments(Source):

    def __init__(self):

        super().__init__()

        self.data = {
            'trace_info': dict(),
            'cpu_state':  None
        }

    def _name(self):

        return 'instruments'

    def _enable(self, item):

        pass

    def _trace(self, duration):

        if platform.system() != 'Darwin':

            sys.exit('ERROR: xcrun is only supported on MacOS.')

        trace_path = self.get_workspace() + 'instruments.trace'

        os.system('xcrun xctrace record --device "" --template "%s/libs/instruments/tracecat.tracetemplate" --time-limit %ds --all-processes --append-run --output %s' % (get_runtime_path(), duration, trace_path))

        if not os.path.exists(trace_path):

            sys.exit('ERROR: Create trace file failed, please check error message.')

        print('Done. (%s)' % trace_path)

    def _parse(self):

        self.__parse_cpu_state()

    def __parse_cpu_state(self):

        # for tunning pandas performance

        results = {
            'start_time':   list(),
            'duration':     list(),
            'end_time':     list(),
            'cpu_id':       list(),
            'cpu_state':    list(),
            'process_id':   list(),
            'process_name': list(),
            'thread_id':    list(),
            'thread_name':  list(),
            'priority':     list(),
        }

        # export xml file

        print('Exporting cpu_state...')

        trace_path = self.get_workspace() + 'instruments.trace'

        cpu_state_path = self.get_workspace() + 'cpu_state.xml'

        if not os.path.exists(cpu_state_path):

            os.system('xcrun xctrace export --input %s --xpath \'/trace-toc/run[@number="1"]/data/table[@schema="cpu-state"]\' --output %s' % (trace_path, cpu_state_path))

            if not os.path.exists(cpu_state_path):

                sys.exit('ERROR: Failed. Please check error message.')

        else:

            print('Already exported (cpu_state.xml), skip.')

        print('Success. (%s)' % cpu_state_path)

        # parse xml

        print('Parsing cpu_state...')

        tree = xml.parse(cpu_state_path)

        root = tree.getroot()

        refs = dict()

        for row in root.iter('row'): # loop for each row
            
            new = {
                'start_time':   None,
                'duration':     None,
                'end_time':     None,
                'cpu_id':       None,
                'cpu_state':    None,
                'process_id':   None,
                'process_name': None,
                'thread_id':    None,
                'thread_name':  None,
                'priority':     None
            }

            for col in row: # loop for each col

                # get ref node

                node = None

                if 'id' in col.attrib:
                    
                    refs[col.attrib['id']] = col

                    node = col

                elif 'ref' in col.attrib:

                    node = refs[col.attrib['ref']]

                # get each data

                if col.tag == 'start-time':
                    
                    new['start_time'] = int(node.text)

                elif col.tag == 'duration':

                    new['duration'] = int(node.text)

                elif col.tag == 'core':

                    new['cpu_id'] = int(node.text)

                elif col.tag == 'core-state':

                    new['cpu_state'] = node.text

                elif col.tag == 'process':

                    new['process_id'] = node.find('pid').attrib['fmt']

                    new['process_name'] = node.attrib['fmt']
                    
                elif col.tag == 'thread':

                    new['thread_id'] = node.find('tid').attrib['fmt']

                    new['thread_name'] = node.attrib['fmt']
                    
                elif col.tag == 'sched-priority':

                    new['priority'] = int(node.text)

            new['end_time'] = new['start_time'] + new['duration']

            for key, val in new.items():

                results[key].append(val)

        # save results

        df = pandas.DataFrame(results)

        df.sort_values(by=['start_time'], inplace=True)

        df.reset_index(drop=True, inplace=True)

        self.data['cpu_state'] = df

        self.data['trace_info']['start_time'] = df.start_time.min()
        
        self.data['trace_info']['end_time'] = df.end_time.max()
        
        self.data['trace_info']['duration'] = self.data['trace_info']['end_time'] - self.data['trace_info']['start_time']

        self.data['trace_info']['cpu_list'] = sorted(df.cpu_id.unique().tolist())

        print('Done.')

    def get_cpu_state(self):

        return self.data['cpu_state'].copy()

    def get_process_list(self):

        return get_unique_list(self.data['cpu_state'], {'process_id': str, 'process_name': str})

    def get_trace_info(self):

        return self.data['trace_info'].copy()