import os
import sys
import pandas

from abc import ABC, abstractmethod

from framework.plotter import Plotter

class Module(ABC):

    def __init__(self):
        
        self.sources = dict()

        self.plotter = Plotter()

        self.workspace = None

        self.results = None

    def init_workspace(self, workspace):

        self.workspace = workspace

    def init_sources(self, sources):

        self.sources = sources

    def init_plotter(self, **kwargs):

        self.plotter.init_plot(**kwargs)

    def invoke_source(self, source_name, items = None):

        if not self.sources:

            raise Exception('Data source is used before init.')

        if source_name not in self.sources:

            raise Exception('Data source "%s" not found.' % source_name)

        source = self.sources[source_name]

        source.enable(items)

        return source

    def invoke_result(self, module_names, return_when_fail = False):

        file_list = list()

        if type(module_names) == str:

            module_names = [module_names]

        for module_name in module_names:

            pickle_file = self.workspace + module_name + '.pkl'

            if os.path.exists(pickle_file):

                return pandas.read_pickle(pickle_file)

            file_list.append(pickle_file)

        if return_when_fail:

            return None

        print('ERROR: Invoke results failed, pickle file not found: ', end='')

        if len(file_list) == 1:

            print(file_list[0])

        else:

            print('')

            for file in file_list:

                print(file)
        
        sys.exit()

    def save(self, pickle_file = None):

        if self.results is None:

            return None

        if not pickle_file:

            pickle_file = self.workspace + self.get_name() + '.pkl'

        self.results.to_pickle(pickle_file)

        return pickle_file

    def load(self, pickle_file = None):

        if not pickle_file:

            pickle_file = self.workspace + self.get_name() + '.pkl'

        if not os.path.exists(pickle_file):

            sys.exit('ERROR: Result pickle file not found. ' + pickle_file)

        self.results = pandas.read_pickle(pickle_file)

        return self.results.copy()

    def export(self, excel_file = None):

        if self.results is None:

            return None

        if len(self.results) < 1048576: # Excel format limit rows

            if not excel_file:

                excel_file = self.workspace + self.get_name() + '.xlsx'

            self.results.to_excel(excel_file)

        else: # Fallback to csv format

            if not excel_file:

                excel_file = self.workspace + self.get_name() + '.csv'

            self.results.to_csv(excel_file)

        return excel_file

    def get_result(self):

        return self.results.copy()

    def trace(self, params):

        self.do_trace(params)

    def parse(self, params):

        self.results = self.do_parse(params)

    def chart(self, params):

        self.do_chart(params, self.results.copy())

    # Virtual function but not requred to be implemented.
    def invoke_sources(self):
        pass

    # Virtual function but not requred to be implemented.
    def invoke_results(self):
        pass

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_desc(self):
        pass

    @abstractmethod
    def get_help(self):
        pass

    def do_trace(self, params):
        pass

    @abstractmethod
    def do_parse(self, params):
        pass

    @abstractmethod
    def do_chart(self, params, df):
        pass