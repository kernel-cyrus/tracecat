# Data sources
from framework.sources.perfetto import Perfetto
from framework.sources.instruments import Instruments
from framework.sources.sysfs import Sysfs
from framework.sources.procfs import Procfs
from framework.sources.profiler import Profiler
from framework.sources.simpleperf import Simpleperf
from framework.sources.ftrace import Ftrace

# Modules
from modules.cpu_load.cpu_load_module import Cpu_load_module
from modules.cpu_load2.cpu_load2_module import Cpu_load2_module
from modules.cpu_load_summary.cpu_load_summary_module import Cpu_load_summary_module
from modules.app_load.app_load_module import App_load_module
from modules.cpu_idle.cpu_idle_module import Cpu_idle_module
from modules.cpu_freq.cpu_freq_module import Cpu_freq_module
from modules.cpu_freq2.cpu_freq2_module import Cpu_freq2_module
from modules.cpu_freq_stat.cpu_freq_stat_module import Cpu_freq_stat_module
from modules.cpu_freq_stat2.cpu_freq_stat2_module import Cpu_freq_stat2_module
from modules.gpu_freq.gpu_freq_module import Gpu_freq_module
from modules.gpu_freq_stat.gpu_freq_stat_module import Gpu_freq_stat_module
from modules.ddr_freq.ddr_freq_module import Ddr_freq_module
from modules.ddr_freq_stat.ddr_freq_stat_module import Ddr_freq_stat_module
from modules.dsu_freq.dsu_freq_module import Dsu_freq_module
from modules.thermal_zone.thermal_zone_module import Thermal_zone_module
from modules.ios_cpu_load.ios_cpu_load_module import Ios_cpu_load_module
from modules.ios_app_load.ios_app_load_module import Ios_app_load_module
from modules.ios_cpu_freq.ios_cpu_freq_module import Ios_cpu_freq_module
from modules.profiler.profiler_module import Profiler_module
from modules.simpleperf.simpleperf_module import Simpleperf_module

SOURCES = [
    Ftrace(),
    Sysfs(),
    Procfs(),
    Perfetto(),
    Instruments(),
    Profiler(),
    Simpleperf(),
]

MODULES = [
    Cpu_load_module(),
    Cpu_load2_module(),
    Cpu_load_summary_module(),
    App_load_module(),
    Cpu_idle_module(),
    Cpu_freq_module(),
    Cpu_freq2_module(),
    Cpu_freq_stat_module(),
    Cpu_freq_stat2_module(),
    Gpu_freq_module(),
    Gpu_freq_stat_module(),
    Ddr_freq_module(),
    Ddr_freq_stat_module(),
    Dsu_freq_module(),
    Thermal_zone_module(),
    Ios_cpu_load_module(),
    Ios_app_load_module(),
    Ios_cpu_freq_module(),
    Profiler_module(),
    Simpleperf_module()
]