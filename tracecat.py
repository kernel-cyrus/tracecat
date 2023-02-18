#!./venv/bin/python3

import os
import sys
import time
import datetime
import matplotlib.pyplot as plt
import pandas
import threading
import argparse

from framework.config import VERSION, CONFIG
from framework.objects import SOURCES, MODULES
from framework.helpers import get_element, get_time, log_current_command

class Tracecat():

    modules = dict()

    sources = dict()

    def __init__(self):

        for module in MODULES:

            self.modules[module.get_name()] = module

        for source in SOURCES:

            self.sources[source.get_name()] = source

    def __get_run_name(self, run_type):

        if run_type == 'NEW':

            now = datetime.datetime.now()

            return now.strftime('%Y%m%d_%H%M%S')

        elif run_type == 'LAST':

            dirs = dict()

            for dname in next(os.walk('./runs'))[1]:

                ctime = os.path.getctime('./runs/' + dname)

                dirs[ctime] = dname

            if not dirs:

                return None

            return dirs[max(dirs.keys())]

        else:

            raise Exception('Invalid run_type.')

    def __get_module(self, module_name):

        if module_name not in self.modules:

            sys.exit('ERROR: Module not found: %s' % module_name)

        return self.modules[module_name]

    def trace(self, mod_list, run_name, options):

        threads = list()

        duration = options['duration']

        if not duration:

            sys.exit('ERROR: You forgot passing option: --duration <duration>')

        duration = get_time(duration, 's')

        if duration < 1:

            sys.exit('ERROR: [duration] should at least be 1s.')

        # Init a run

        if not run_name:

            run_name = self.__get_run_name('NEW')

        run_folder = './runs/%s/' % run_name

        if os.path.exists(run_folder):

            sys.exit('ERROR: Path already exsist: ' + run_folder)

        print('Using: %s' % run_folder)

        # Invoke sources from module

        for mod in mod_list:

            module = self.__get_module(mod['module'])

            module.init_sources(self.sources)

            module.invoke_sources()

            module.trace(mod['params'])

        # Invoke sources from source

        for source in self.sources.values():

            if source.is_enable():

                source.init_invoke(self.sources)

                source.invoke_sources()

        # Create data source threads

        for source in self.sources.values():

            if source.is_enable():

                source_folder = run_folder + source.get_name() + '/'

                source.init_workspace(source_folder)

                thread = threading.Thread(target=source.trace, args=(duration,))

                threads.append({
                    'name': source.get_name(),
                    'thread': thread
                })

                # Call pre trace

                source.pre_trace(duration)

        # Run data source threads

        for thread in threads:

            print('Create thread: ' + thread['name'])

            thread['thread'].start()

        # Wati for completion

        for thread in threads:

            thread['thread'].join()

            print('Thread finished: ' + thread['name'])

        # Call post trace

        for source in self.sources.values():

            if source.is_enable():

                source.post_trace(duration)

        log_current_command(run_folder + '/log.txt')

    def parse(self, mod_list, run_name, options):

        # Init a run

        if not run_name:

            run_name = self.__get_run_name('LAST')

            if not run_name:

                sys.exit('ERROR: Trace data not found, maybe you need run trace first.')

        run_folder = './runs/%s/' % run_name

        if not os.path.exists(run_folder):

            sys.exit('ERROR: Path not exsist: ' + run_folder)

        print('Using: %s' % run_folder)

        # Invoke sources

        for mod in mod_list:

            module = self.__get_module(mod['module'])

            module.init_sources(self.sources)

            module.invoke_sources()

        for source in self.sources.values():

            if source.is_enable():

                source.init_invoke(self.sources)

                source.invoke_sources()
                
        # Run source parsing

        for source in self.sources.values():

            if not source.is_enable():

                continue

            source_folder = run_folder + source.get_name() + '/'

            if not os.path.exists(source_folder):

                sys.exit('ERROR: Path not found: %s' % source_folder)

            source.init_workspace(source_folder)

            source.parse()

        # Run module parsing

        module_folder = run_folder + 'modules/'

        if not os.path.exists(module_folder):

            os.makedirs(module_folder)

        for mod in mod_list:

            module = self.__get_module(mod['module'])

            print('Parsing %s...' % module.get_name())

            module.init_workspace(module_folder)

            module.invoke_results()

            module.parse(mod['params'])

            print('Saving pickle file...')

            file_path = module.save()

            if file_path:

                print('Pickle file saved: %s' % file_path)

            print('Export excel file...')

            file_path = module.export()

            if file_path:

                if file_path[-4:] == '.csv':
                    
                    print('WARNING: Too many data, fallback to csv format.')

                print('Excel file saved: %s' % file_path)

        log_current_command(run_folder + '/log.txt')

        print('Done.')

    def chart(self, mod_list, run_name, options):

        # Init a run

        if not run_name:

            run_name = self.__get_run_name('LAST')

            if not run_name:

                sys.exit('ERROR: Trace data not found, maybe you need run trace first.')
        
        run_folder = './runs/%s/' % run_name

        if not os.path.exists(run_folder):

            sys.exit('ERROR: Path not exsist. ' + run_folder)

        print('Using: %s' % run_folder)

        # Plot charts

        axis = plt.gca()

        figure = plt.gcf()

        title = ''

        module_folder = run_folder + 'modules/'

        for idx, mod in enumerate(mod_list):

            module = self.__get_module(mod['module'])

            print('Loading %s...' % module.get_name())

            module.init_workspace(module_folder)

            result = module.load()

            if result.empty:

                sys.exit('ERROR: Nothing to plot.')

            print('Ploting %s...' % module.get_name())

            module.init_plotter(ax=axis, secondary_y=idx>0)

            module.chart(mod['params'])

            title += ' / ' + module.get_name() if title else module.get_name()

        axis.set_title(title)

        plt.gcf().canvas.set_window_title(run_name + ' - ' + title)

        plt.tight_layout()

        export = options['export']

        if export is not None:

            if not export:

                image_size = None

            else:

                image_args = export.split(',')

                if len(image_args) != 2 or not image_args[0].isdigit() or not image_args[1].isdigit():

                    sys.exit('ERROR: Invalid [image_size] format, please type <width>,<height>. (e.g. 1024,768)')

                image_size = {'width': int(image_args[0]), 'height': int(image_args[1])}
            
            dpi = 100

            image_file = ''

            for mod in mod_list:

                if image_file:

                    image_file += '_'

                image_file += mod['module']

                if mod['params']:

                    param = '(' + ','.join(mod['params']) + ')'

                    param = param.replace('/', '_')

                    image_file += param

            image_file = module_folder + image_file + '.png'

            if image_size:

                figure.set_size_inches(image_size['width'] / dpi, image_size['height'] / dpi)

                plt.savefig(image_file, dpi=dpi)

            else:
                plt.savefig(image_file)

            print('Save chart as image: %s' % image_file)

            log_current_command(run_folder + '/log.txt')

            print('Done.')

        else:
            
            start = time.time()
            
            plt.show()
            
            end = time.time()
            
            if end - start < 1:
                
                print('ERROR: It seems something wrong with the plot, please check the error message.')

                print('To solve this issue, you may run: "sudo apt install python3-tk" and try again.')

            else:
                print('Done.')

    def print_help(self):

        text  = '\nTracecat %s\n' % VERSION
        text += '=========================\n'

        text += '\nBasic Format:\n'
        text += '    tracecat "trace:<module>,..." <run_name>\n'
        text += '        --duration, -d <time>              trace duration.\n'
        text += '        --sampling-period, -s <time>       sampling period.\n'
        text += '        --sampling-mode <mode>             sampling "online" or "offline".\n'
        text += '        --execute-su                       excute su before any command.\n'
        text += '    tracecat "parse:<module>(params),..." <run_name>\n'
        text += '    tracecat "chart:<module>(params),..." <run_name>\n'
        text += '        --export, -e <width,height>        save chart to image file.\n'

        text += '\nAvailable Modules:\n'

        for module in self.modules.keys():

            text += '    ' + (self.modules[module].get_name() + ':').ljust(18) + self.modules[module].get_desc() + '\n'

        text += '\nExamples:\n'
        text += '    > tracecat -h <module>\n'
        text += '    To see more details and module\'s available params.\n\n'
        text += '    > tracecat "trace:cpu_load,cpu_freq" findx2_pubg --duration 10s\n'
        text += '    Start tracing for 10s and save trace file to ./runs/findx2_pubg \n\n'
        text += '    > tracecat "parse:cpu_load(100ms),cpu_freq" findx2_pubg \n'
        text += '    Parse cpu load (100ms window) and cpu freq, export result to excel.\n\n'
        text += '    > tracecat "chart:cpu_load(0-3,4-6,7),cpu_freq(0,4,7)" findx2_pubg \n'
        text += '    Plot cpu avarage load and cpu freq chart for each cluster. \n\n'
        text += '    > tracecat "chart:cpu_load" findx2_pubg --export 1024*768 \n'
        text += '    Save chart image to ./runs/findx2_pubg/cpu_load.png (width:1024, height:768) \n\n'
        text += '    > tracecat "trace:cpu_load2,cpu_freq2,gpu_freq,ddr_freq" findx2_pubg -s 100ms \n'
        text += '    Sampling cpu load, cpu freq, gpu freq, ddr freq from fs node, set sampling period to 100ms. \n'

        text += '\nContact:\n'
        text += '    Github: https://github.com/kernel-cyrus/tracecat\n'
        text += '    Author: Cyrus Huang  Email: cyrus@kernel-tour.org\n'

        print(text)

    def print_module_help(self, module):

        text  = '\n' + module.get_name() + '\n'
        text += '-------------------------\n'
        text += module.get_desc() + '\n'
        text += module.get_help() + '\n'

        print(text)

    def __parse_mod_list(self, modline):

        mod_list = list()

        pos = 0

        parsing_params = False

        module = None
        params = list()

        for idx, char in enumerate(modline + ','):

            if not parsing_params and char == '(':

                parsing_params = True

                module = modline[pos:idx].strip()

                pos = idx + 1

            elif parsing_params and char == ')':

                parsing_params = False

                param = modline[pos:idx].strip()

                if param:

                    params.append(param)

                pos = idx + 1

            elif parsing_params and char == ',':

                param = modline[pos:idx].strip()

                if param:

                    params.append(param)

                pos = idx + 1

            elif not parsing_params and char == ',':

                if not module:
                    
                    module = modline[pos:idx].strip()

                if module:

                    mod_list.append({
                        'module': module,
                        'params': params
                    })

                module = None
                params = list()

                pos = idx + 1

            else:

                pass
                
        if module:

            mod_list.append({
                'module': module,
                'params': params
            })
        
        return mod_list

    def __parse_runline(self, runline):

        if not runline:

            return None, None

        args = runline.split(':', 1)

        run_mode = get_element(args, 0)

        if not run_mode:

            return None, None

        mod_line = get_element(args, 1)

        if not mod_line:

            return run_mode, None

        mod_list = self.__parse_mod_list(mod_line)

        return run_mode, mod_list

    def parse_command(self, args):

        # Run help

        first_param = get_element(args, 1)

        if not first_param or first_param in ['-h', 'help', '-help', '--help']:

            module = get_element(args, 2)

            if module:
                self.print_module_help(self.__get_module(module))
            else:
                self.print_help()

            sys.exit()

        # Parse run line

        run_line = first_param

        run_mode, mod_list = self.__parse_runline(run_line)

        # Parse run name

        run_name = get_element(args, 2)

        if run_name and run_name[0] == '-':

            run_name = None

        # Parse args

        parser = argparse.ArgumentParser(add_help=False)

        parser.add_argument('--duration', '-d')

        parser.add_argument('--export', '-e', type = str, nargs='?', const='')

        parser.add_argument('--sampling-period', '-s')

        parser.add_argument('--execute-su', '-su', type = int, nargs='?', const=True)

        parser.add_argument('--sampling-mode', '-sm')

        options, unknown = parser.parse_known_args(sys.argv[1:])

        options = vars(options)

        # Set global options

        if options['sampling_period']:

            CONFIG['SAMPLING_PERIOD'] = get_time(options['sampling_period'], 'ms')

        if options['sampling_mode']:

            sampling_mode = options['sampling_mode'].upper()

            if sampling_mode not in ['ONLINE', 'OFFLINE']:

                sys.exit('ERROR: Invalid sampling mode: "%s", should be "ONLINE" or "OFFLINE"' % sampling_mode)

            CONFIG['SAMPLING_MODE'] = sampling_mode

        if options['execute_su']:

            CONFIG['EXEC_WITH_SU'] = options['execute_su']

        if run_mode == 'trace':

            if not mod_list:

                sys.exit('ERROR: Invalid [module list], please check your input.')

            self.trace(mod_list, run_name, options)

        elif run_mode == 'parse':

            if not mod_list:

                sys.exit('ERROR: Invalid [module list], please check your input.')

            self.parse(mod_list, run_name, options)

        elif run_mode == 'chart':

            if not mod_list:

                sys.exit('ERROR: Invalid [module list], please check your input.')

            self.chart(mod_list, run_name, options)

        else:
            self.print_help()

            sys.exit('ERROR: Invalid command, please run tracecat -h for help.')

if __name__ == "__main__":

    tracecat = Tracecat()

    tracecat.parse_command(sys.argv)
