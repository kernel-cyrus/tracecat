import os
import traceback

from abc import ABC, abstractmethod
from framework.helpers import handle_thread_exceptions

class Source(ABC):

    def __init__(self):

        self.workspace = None

        self.status = False

        self.sources = None

    def init_workspace(self, workspace):
        
        if not os.path.exists(workspace):

            os.makedirs(workspace)

        self.workspace = workspace

    def init_invoke(self, sources):

        self.sources = sources

    def enable(self, items = None):

        if items:

            if type(items) != list:

                items = [items]

            for item in items:
                
                self._enable(item)

        self.status = True

    def config(self, item, conf):

        self._config(item, conf)

    def is_enable(self):
        
        return self.status

    def get_name(self):

        return self._name()

    def get_workspace(self):

        if not self.workspace:

            raise Exception('Workspace is used before init.')

        return self.workspace

    @handle_thread_exceptions
    def trace(self, duration):

        if not self.is_enable():

            raise Exception('Data source run before enable.')

        return self._trace(duration)
            
    def pre_trace(self, duration):

        self._pre_trace(duration)

    def post_trace(self, duration):

        self._post_trace(duration)

    def parse(self):

        if not self.is_enable():

            raise Exception('Data source run before enable.')

        return self._parse()

    def invoke_source(self, source_name, items = None):

        if not self.sources:

            raise Exception('Data source is used before init.')

        if source_name not in self.sources:

            raise Exception('Data source "%s" not found.' % source_name)

        source = self.sources[source_name]

        source.enable(items)

        return source

    def invoke_sources(self):
        pass

    @abstractmethod
    def _name(self):
        pass

    @abstractmethod
    def _enable(self, item):
        pass

    def _config(self, item, conf):
        
        raise Exception('Should be implemented or not called.')

    @abstractmethod
    def _trace(self, duration):
        pass

    @abstractmethod
    def _parse(self):
        pass

    def _pre_trace(self, duration):
        pass

    def _post_trace(self, duration):
        pass