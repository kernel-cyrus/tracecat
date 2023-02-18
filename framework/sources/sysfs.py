from framework.sources.basefs import Basefs

class Sysfs(Basefs):

    def __init__(self):

        super().__init__()

    def name(self):

        return 'sysfs'

    def metrics(self):

        metrics = {

            'cpu_freq': {
                'type': 'DATA',
                'profiles': [
                    {'nodes': '/sys/devices/system/cpu/cpu?/cpufreq/scaling_cur_freq',      'parser': lambda x, y: self.batch_nodes_parser(x, y, int)}, # FindX2, Mate40 (kHz)
                ]
            },

            'cpu_freq_table': {
                'type': 'INFO',
                'profiles': [
                    {'nodes': '/sys/devices/system/cpu/cpu?/cpufreq/scaling_available_frequencies', 'parser': lambda x, y: self.batch_nodes_parser(x, y, lambda z: [int(freq) for freq in z.split()])}, # FindX2, Mate40 (kHz)
                ]
            },

            'gpu_freq': {
                'type': 'DATA',
                'profiles': [
                    {'nodes': '/sys/kernel/gpu/gpu_clock',                                  'parser': lambda x : int(x) * 1000},        # FindX2 (kHz)
                    {'nodes': '/sys/class/kgsl/kgsl-3d0/devfreq/cur_freq',                  'parser': lambda x : int(int(x) / 1000)},   # FindX2 (kHz)
                    {'nodes': '/sys/class/devfreq/gpufreq/cur_freq',                        'parser': lambda x : int(int(x) / 1000)},   # Mate40 (kHz)
                    {'nodes': '/sys/devices/platform/1c500000.mali/cur_freq',               'parser': lambda x : int(x)},               # Pixel6Pro (kHz)
                    {'nodes': '/sys/kernel/ged/hal/current_freqency',                       'parser': lambda x : int(x.split()[1])},    # M? (kHz) # Spelling mistake
                    {'nodes': '/sys/class/devfreq/13000000.mali/cur_freq',                  'parser': lambda x : int(int(x) / 1000)},   # M? (kHz) # Seems never change
                ]
            },

            'gpu_freq_table': {
                'type': 'INFO',
                'profiles': [
                    {'nodes': '/sys/kernel/gpu/gpu_freq_table',                             'parser': lambda x : [int(freq) * 1000 for freq in x.split()]},        # FindX2 (kHz)
                    {'nodes': '/sys/class/devfreq/gpufreq/available_frequencies',           'parser': lambda x : [int(int(freq) / 1000) for freq in x.split()]},   # Mate40 (kHz)
                    {'nodes': '/sys/devices/platform/1c500000.mali/available_frequencies',  'parser': lambda x : [int(freq) for freq in x.split()]},               # Pixel6Pro (kHz)
                    {'nodes': '/sys/class/devfreq/13000000.mali/available_frequencies',     'parser': lambda x : [int(int(freq) / 1000) for freq in x.split()]},   # M? (kHz)
                ]
            },

            'ddr_freq': {
                'type': 'DATA',
                'profiles': [
                    {'nodes': '/sys/devices/platform/1c00f000.dvfsrc/helio-dvfsrc/dvfsrc_dump', 'parser': self.__parse_helio_ddr_freq}, # M*9000 (kHz)
                    {'nodes': '/sys/kernel/debug/clk/measure_only_mccc_clk/clk_measure',    'parser': lambda x : int(int(x) / 1000)},   # FindX2 (kHz)
                    {'nodes': '/proc/clk/mc_cc_debug_mux/clk_measure',                      'parser': lambda x : int(int(x) / 1000)},   # 8+ (kHz)
                    {'nodes': '/sys/class/devfreq/ddrfreq/cur_freq',                        'parser': lambda x : int(int(x) / 1000)},   # Mate40 (kHz)
                    {'nodes': '/sys/class/devfreq/17000010.devfreq_mif/cur_freq',           'parser': lambda x : int(x)},               # Pixel6Pro (kHz)
                    {'nodes': '/sys/class/devfreq/mtk-dvfsrc-devfreq/cur_freq',             'parser': lambda x : int(int(x) / 1000)},   # M? (kHz)
                    {'nodes': '/sys/devices/system/cpu/bus_dcvs/DDR/cur_freq',              'parser': lambda x : int(x)},               # 8GEN1 (kHz)
                    

                ]
            },

            'ddr_freq_table': {
                'type': 'INFO',
                'profiles': [
                    {'nodes': '/sys/class/devfreq/ddrfreq/available_frequencies',               'parser': lambda x : [int(int(freq) / 1000) for freq in x.split()]},   # Mate40 (kHz)
                    {'nodes': '/sys/class/devfreq/17000010.devfreq_mif/available_frequencies',  'parser': lambda x : [int(freq) for freq in x.split()]},               # Pixel6Pro (kHz)
                    {'nodes': '/sys/class/devfreq/mtk-dvfsrc-devfreq/available_frequencies',    'parser': lambda x : [int(int(freq) / 1000) for freq in x.split()]},   # M? (kHz)
                    {'nodes': '/sys/devices/system/cpu/bus_dcvs/DDR/available_frequencies',     'parser': lambda x : [int(freq) for freq in x.split()]},               # 8GEN1 (kHz)
                ]
            },

            'dsu_freq': {
                'type': 'DATA',
                'profiles': [
                    {'nodes': '/sys/class/devfreq/18590000.qcom,devfreq-l3:qcom,cpu?-cpu-l3-lat/cur_freq', 'parser': lambda x, y: self.batch_nodes_parser(x, y, lambda z: int(int(z) / 1000))},   # FindX2 (kHz)
                ]
            },

            'thermal_zone': {
                'type': 'DATA',
                'profiles': [
                    {'nodes': '/sys/class/thermal/thermal_zone*/temp',                      'parser': lambda x, y: self.batch_nodes_parser(x, y, lambda z: int(z) if z.lstrip('-').isdigit() else 0)},   # FindX2
                    {'nodes': '/sys/devices/virtual/thermal/thermal_zone*/temp',            'parser': lambda x, y: self.batch_nodes_parser(x, y, lambda z: int(z) if z.lstrip('-').isdigit() else 0)},   # Mate40Pro
                ]
            },
        }

        return metrics

    def __parse_helio_ddr_freq(self, output):

        lines = output.split('\n')

        for line in lines:

            if line[:3] == 'DDR' and line[-3:] == 'khz':

                args = line.split()

                ddr_freq = int(args[2])

        return ddr_freq
