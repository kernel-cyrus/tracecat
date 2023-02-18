# User Guide

Tracecat是一个模块化设计的通用Trace解析框架。

支持从Systrace、Perfetto、Ftrace、Simpleperf、Dumpsys、Sysfs、Procfs、iPhone instruments、SnapdragonProfiler等数据源并行采集、解析数据，并生成Excel及各类分析图表。

你可以基于它轻松扩展Trace解析功能，也可以直接将他作为工具使用。

## 快速上手

tracecat由trace, parse, chart三个命令和各类数据module（模块）组成：

- trace：命令从手机抓取原始数据

- parse：命令解析出对应的数据

- chart：命令生成图表

每个module就是一种类型的数据。所有原始数据和生成的数据，都会保存在./runs/<xxx>文件夹下。

tracecat下载后，解压即可直接运行，无需任何额外配置。

手机连接，确定adb连接ok，命令行进入tracecat目录后，可以通过下面一组常用命令5分钟快速上手。

```
tracecat
```

会直接显示tracecat的介绍和帮助，支持的模块

```
tracecat -h cpu_load2
```

查看cpu_load2模块的详细帮助和参数

```
tracecat "trace:cpu_load2" test -d 10s
```

从手机抓取cpu占用率(从proc下采集数据)，抓取10s，数据存入./runs/test文件夹下（然后你可以去文件夹拿到原始trace文件）

```
tracecat "parse:cpu_load2" test
```

从抓取的数据中解析出cpu占用率，解析后会在./runs/modules文件夹下生成cpu_load2.pkl和cpu_load2.xls两个文件

你可以用excel直接打开.xls文件来制作数据，也可以用python加载.pkl文件，做二次处理（见：更多功能 / 使用pkl文件数据）

```
tracecat "chart:cpu_load2" test
```

如果你需要将数据以图表形式呈现，执行这条命令，会自动生成图表，可以放大缩小拖拽。

```
tracecat "chart:cpu_load2(0-3,4-6,7)" test
```

你也可以在模块中添加参数，比如显示cpu 0-3, 4-6和7的平均占用率

```
tracecat "chart:cpu_load2" test --export 1024,768
```

将图表导出成png文件，文件保存在./runs/modules/cpu_load2.png

## 更多功能

上面的例子中只演示了cpu_load2这个模块，tracecat的每种数据都实现为一个独立模块，用tracecat -h可以看到所有模块

每个模块，在parse和chart命令中，都支持传入参数，可以用tracecat -h \<module\>来查看对应module的参数

```
tracecat -h cpu_load
```

tracecat支持多数据并行抓取，你可以在命令中添加所有你想抓取的模块

```
tracecat "trace:cpu_load,cpu_load_stat,cpu_freq,cpu_freq_stat,ddr_freq,ddr_freq_stat" test -d 10s
```

抓取后全部解析，其中cpu占用率以10ms的粒度统计

```
tracecat "parse:cpu_load(10ms),cpu_load_stat,cpu_freq,cpu_freq_stat,ddr_freq,ddr_freq_stat" test
```

可以多个图表叠加显示

```
tracecat "chart:cpu_load(0-3,4-6,7),cpu_freq(0,4,7)" test
```

利用&同时启动多个图表

```
tracecat "chart:cpu_load" test &
tracecat "chart:cpu_freq" test &
```

利用trace功能抓perfetto

```
tracecat "cpu_load" test -d 10s
```

抓取结束后，可以直接将./runs/test/perfetto/perfetto.trace拖入https://ui.perfetto.dev/#!/打开

为了抓去更多额外trace，可以手动配置perfetto tracing config：

```
vim ./configs/perfetto/perfetto.conf
```

这些设置会自动与tracecat默认抓取设置合并。

tracecat在大量抓取场景数据后，支持批量解析和批量生成图片

```
run_all "parse:cpu_load,cpu_freq"
run_all "chart:cpu_laod,cpu_freq"
```

这个命令会将runs/所有文件夹解析并生成图片文件

有些机器在adb shell后需要手动执行su，对于这些机器，抓取时需要添加--execute-su参数

```
tracecat "trace:cpu_load" test -d 10s --execute-su
```

使用在线采样或离线采样，目前默认为离线方式，资源占用更少，但是作为备选方案，仍然支持在线采样

```
tracecat "trace:cpu_load2" test -d 10s --sampling-mode online
```

对于以采样方式获取的数据，可以指定采样频率

```
tracecat "trace:cpu_load2,cpu_freq2" test -d 10s -s 10ms          # 所有采样模块均以10ms粒度采样
tracecat "trace:cpu_load2(50ms),cpu_freq2(10ms)" test -d 10s      # cpu_load2以50ms采样，cpu_freq2以10ms采样
```

## 模块详解

下面样例中省略了文件夹名字、抓取时间等参数

**cpu_load**

从perfetto的trace中解析CPU占用率

```
tracecat "trace:cpu_load"                 # 抓取perfetto trace
tracecat "parse:cpu_load"                 # 以1s粒度解析占用率
tracecat "parse:cpu_load(100ms)"          # 以100ms粒度解析占用率
tracecat "chart:cpu_load"                 # 显示各cpu占用率
tracecat "chart:cpu_load(0)"              # 只显示cpu 0的占用率
tracecat "chart:cpu_load(0-4,5-6,7)"      # 显示平均占用率
```

\* 不建议长时间抓取，因为生成的trace文件可能过大，长时间抓取请使用cpu_load2

**cpu_load2**

从procfs采样CPU占用率

```
tracecat "trace:cpu_load2"                 # 以500ms粒度采样（默认）
tracecat "trace:cpu_load2(100ms)"          # 以100ms粒度采样（模块设置）
tracecat "trace:cpu_load2" -s 100ms        # 以100ms粒度采样（全局设置）
tracecat "parse:cpu_load2"                 # 解析
tracecat "chart:cpu_load2"                 # 显示各cpu占用率
tracecat "chart:cpu_load2(0)"              # 只显示cpu 0的占用率
tracecat "chart:cpu_load2(0-4,5-6,7)"      # 显示平均占用率
```

**cpu_load_summary**

统计该场景cpu占用率的最大、最小、平均值

```
tracecat "trace:cpu_load"                  # 先要抓取cpu_load或者cpu_load2
tracecat "parse:cpu_load,cpu_load_summary" # 从cpu_load或cpu_load2的解析结果中计算统计结果
tracecat "chart:cpu_load_summary"          # 显示柱状图
```

**app_load**

某个进程的CPU占用率

```
tracecat "trace:app_load"                  # 抓取perfetto trace
tracecat "parse:app_load"                  # 解析app_load
tracecat "parse:app_load(100ms)"           # 以100ms粒度解析app_load
tracecat "chart:app_load"                  # 显示所有process
tracecat "chart:app_load(1532)"            # 显示所有pid为1532的进程各核占用率
tracecat "chart:app_load(pubg)"            # 显示名字包含pubg的进程各核占用率
```

\* 不建议长时间抓取，因为生成的trace文件可能过大

**cpu_idle**

从perfetto的trace中解析CPU idle state (C-STATE)

```
tracecat "trace:cpu_idle"                  # 抓取perfetto trace
tracecat "parse:cpu_idle"                  # 解析cpu_idle
tracecat "chart:cpu_idle"                  # 显示所有cpu的idle state曲线
tracecat "chart:cpu_idle(0)"               # 显示cpu 0的idle state曲线
```

**cpu_freq**

从perfetto的trace中解析CPU频率

```
tracecat "trace:cpu_freq"                  # 抓取perfetto trace
tracecat "parse:cpu_freq"                  # 解析cpu_freq
tracecat "chart:cpu_freq"                  # 显示所有cpu的频率曲线
tracecat "chart:cpu_freq(0)"               # 只显示cpu 0的频率曲线
tracecat "chart:cpu_freq(0,4,7)"           # 显示cpu0,4,7的频率曲线(cluster)
```

**cpu_freq_stat**

统计cpu各频点及C-STATE运行时间占比（基于cpu_freq, cpu_idle）

```
tracecat "trace:cpu_freq,cpu_idle,cpu_freq_stat"      # 抓取
tracecat "parse:cpu_freq,cpu_idle,cpu_freq_stat"      # 解析
tracecat "chart:cpu_freq_stat"                        # 生成柱状图
```

\* 如果未抓取cpu_idle，则只解析频点的时间占比，不包含C-STATE信息

**cpu_freq2**

从sysfs采样CPU频率

```
tracecat "trace:cpu_freq2"                 # 以500ms粒度采样（默认）
tracecat "trace:cpu_freq2(100ms)"          # 以100ms粒度采样（模块设置）
tracecat "trace:cpu_freq2" -s 100ms        # 以100ms粒度采样（全局设置）
tracecat "parse:cpu_freq2"                 # 解析
tracecat "chart:cpu_freq2"                 # 显示所有cpu的频率曲线
tracecat "chart:cpu_freq2(0)"              # 只显示cpu 0的频率曲线
tracecat "chart:cpu_freq2(0,4,7)"          # 显示cpu0,4,7的频率曲线(cluster)
```

**cpu_freq_stat2**

统计cpu各频点运行时间占比（基于cpu_freq2）

```
tracecat "trace:cpu_freq2,cpu_freq_stat2"  # 抓取
tracecat "parse:cpu_freq2,cpu_freq_stat2"  # 解析
tracecat "chart:cpu_freq_stat2"            # 生成柱状图
```

**gpu_freq**

从sysfs采样GPU频率

```
tracecat "trace:gpu_freq"                  # 以500ms粒度采样（默认）
tracecat "trace:gpu_freq(100ms)"           # 以100ms粒度采样（模块设置）
tracecat "trace:gpu_freq" -s 100ms         # 以100ms粒度采样（全局设置）
tracecat "parse:gpu_freq"                  # 解析
tracecat "chart:gpu_freq"                  # 显示GPU频率曲线
```

**gpu_freq_stat**

统计gpu各频点运行时间占比（基于gpu_freq）

```
tracecat "trace:gpu_freq,gpu_freq_stat"    # 抓取
tracecat "parse:gpu_freq,gpu_freq_stat"    # 解析
tracecat "chart:gpu_freq_stat"             # 生成柱状图
```

**ddr_freq**

从sysfs采样GPU频率

```
tracecat "trace:ddr_freq"                  # 以500ms粒度采样（默认）
tracecat "trace:ddr_freq(100ms)"           # 以100ms粒度采样（模块设置）
tracecat "trace:ddr_freq" -s 100ms         # 以100ms粒度采样（全局设置）
tracecat "parse:ddr_freq"                  # 解析
tracecat "chart:ddr_freq"                  # 显示GPU频率曲线
```

ddr_freq_stat:

统计ddr各频点运行时间占比（基于ddr_freq）

```
tracecat "trace:ddr_freq,ddr_freq_stat"    # 抓取
tracecat "parse:ddr_freq,ddr_freq_stat"    # 解析
tracecat "chart:ddr_freq_stat"             # 生成柱状图
```

**ios_cpu_load**

iPhone CPU占用率

```
tracecat "trace:ios_cpu_load"              # 抓取instruments trace
tracecat "parse:ios_cpu_load"              # 以1s粒度解析占用率
tracecat "parse:ios_cpu_load(100ms)"       # 以100ms粒度解析占用率
tracecat "chart:ios_cpu_load"              # 显示各cpu占用率
tracecat "chart:ios_cpu_load(0)"           # 只显示cpu 0的占用率
tracecat "chart:ios_cpu_load(0-4,5-6,7)"   # 显示平均占用率
```

\* 需要在MacOS运行，需要安装xcode软件

**ios_app_load**

iPhone某个进程的CPU占用率

```
tracecat "trace:ios_app_load"              # 抓取instruments trace
tracecat "parse:ios_app_load"              # 解析app_load
tracecat "parse:ios_app_load(100ms)"       # 以100ms粒度解析app_load
tracecat "chart:ios_app_load"              # 显示所有process
tracecat "chart:ios_app_load(1532)"        # 显示所有pid为1532的进程各核占用率
tracecat "chart:ios_app_load(pubg)"        # 显示名字包含pubg的进程各核占用率
```

\* 需要在MacOS运行，需要安装xcode软件

**ios_cpu_freq**

iPhone CPU频率（Hack方式，实验功能）

\* 不建议使用

**thermal_zone**

从sysfs采样thermal信息

```
tracecat "trace:thermal_zone"              # 以500ms粒度采样所有thermal节点（默认）
tracecat "trace:thermal_zone(0,1,2)" -s 1s # 以1s粒度采样0,1,2三个zone（设置全局采样频率为1s）
tracecat "trace:thermal_zone(0,1,2|1s)"    # 以1s粒度采样0,1,2三个zone（设置模块采样频率为1s）
tracecat "parse:thermal_zone"              # 解析
tracecat "chart:thermal_zone"              # 显示所有thermal曲线
tracecat "chart:thermal_zone(0,1,2)"       # 显示0,1,2三个zone曲线
```

\* 由于大部分手机thermal节点比较多，建议尽量降低采样频率（>500ms）

**dsu_freq**

从sysfs采样DSU频率

```
tracecat "trace:dsu_freq"                  # 以500ms粒度采样（默认）
tracecat "trace:dsu_freq(100m)"            # 以100ms粒度采样（模块设置）
tracecat "trace:dsu_freq" -s 100ms         # 以100ms粒度采样（全局设置）
tracecat "parse:dsu_freq"                  # 解析
tracecat "chart:dsu_freq"                  # 显示DSU频率曲线
```

**simpleperf**

从simpleperf stat统计simpleperf events，支持全局采样和APP采样两种模式

全局采样：

```
adb shell simpleperf list                                         # 获取手机支持的所有event
tracecat "trace:simpleperf(cache-misses,cpu-cycles)"              # 以500ms粒度全局采样（默认）
tracecat "trace:simpleperf(cache-misses,cpu-cycles|100ms)"        # 以100ms粒度全局采样
```

\* 全局采样包括各个cpu的单独统计数据

APP采样：

```
adb shell pm list package                                         # 获取所有APP包名
tracecat "trace:simpleperf(com.android.dialer|cache-misses|100ms)"# 以100ms粒度只采样APP:com.android.dialer
```

\* APP采样只包括所有cpu的总和数据，不包括单独cpu的数据

解析和显示：

```
tracecat "parse:simpleperf"                                       # 解析所有抓取的event
tracecat "parse:simpleperf(cache-misses,cpu-cycles)"              # 解析部分抓取的event
tracecat "chart:simpleperf"                                       # 显示所有event的曲线
tracecat "chart:simpleperf(cache-misses,cpu-cycles)"              # 显示部分event的曲线
tracecat "chart:simpleperf(cache-misses(cpu0),cpu-cycles(cpu0))"  # 显示某个核的event的曲线
```

**profiler**

半自动方式抓取、解析SnapdragonProfiler提供的所有数据

```
tracecat -h profiler
```

查看所有支持解析的数据类型

```
tracecat "trace:profiler(cpu_branch_miss),profiler(cpu_cache_miss),profiler(cpu_clock)"
```

抓取cpu_branch_miss, cpu_cache_miss, cpu_clock，开始后命令行会进入等待，请手动运行profiler，并在profiler中启动这些数据的抓取，然后在命令行按y继续。

抓取结束后，命令行再次进入等待，请手动停止profiler，并将结果导出到./runs/xxx/profiler/profiler.csv，然后按y继续。

```
tracecat "parse:profiler(cpu_branch_miss),profiler(cpu_cache_miss),profiler(cpu_clock)"
```

解析出cpu_branch_miss, cpu_cache_miss, cpu_clock

```
tracecat "chart:profiler(cpu_branch_miss)"
```

显示cpu_branch_miss的图表

\* 需要PC端安装高通Profiler工具

## 使用pkl文件数据

pkl文件为pandas dataframe数据，可以用pandas加载后，进行二次处理：

```
import pandas

df = pandas.read_pickle('.../cpu_load2.pkl')

print(df)
```

如果你不喜欢用dataframe处理数据，也可以将dataframe转换为正常的dict数组：

```
dicts = df.to_dict('records')
```

pandas的数据处理功能非常丰富，更多使用方法请查阅pandas的user guide。

## Tips

- Windows下使用tracecat运行，Linux下使用./tracecat运行

- trace 功能做了防止意外覆盖的处理，如果runs下已经有对应文件夹，将提示出错，请手动删除文件夹或改名运行

## Contact

Author: Cyrus Huang

Github: <https://github.com/kernel-cyrus/tracecat>