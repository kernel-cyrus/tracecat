VERSION = '0.8.3'

CONFIG = {
    'REMOTE_ROOT': '/data/local/tmp/tracecat',
    'SAMPLING_MODE': 'OFFLINE',  # Sampler working mode, ONLINE or OFFLINE
    'SAMPLING_PERIOD': 500,      # Sampling period(ms), 500ms by default
    'EXEC_WITH_SU': False,       # Execute "su" before run any command
    'FTRACE_BUFFER_SIZE': 2048   # Size of ftrace buffer (kb)
}