# Test 1
python3 tracecat.py "trace:cpu_load,cpu_freq,cpu_idle,cpu_load2,cpu_freq2,cpu_freq_stat,cpu_freq_stat2,ddr_freq,ddr_freq_stat,gpu_freq,gpu_freq_stat,simpleperf(cache-misses|500ms),thermal_zone(0,1,2,3|1s)" -d 5s -s 100ms
python3 tracecat.py "parse:cpu_load,cpu_freq,cpu_idle,cpu_load2,cpu_freq2,cpu_freq_stat,cpu_freq_stat2,ddr_freq,ddr_freq_stat,gpu_freq,gpu_freq_stat,simpleperf,thermal_zone"

sleep 5

# Test 2
python3 tracecat.py "trace:cpu_load,cpu_freq,cpu_idle,cpu_load2(10ms),cpu_freq2,cpu_freq_stat,cpu_freq_stat2,ddr_freq(20ms),ddr_freq_stat,gpu_freq(30ms),gpu_freq_stat,simpleperf(branch-misses,bus-cycles,cache-misses,cache-references,cpu-cycles,instructions,stalled-cycles-backend,stalled-cycles-frontend,branch-load-misses,branch-loads,dTLB-load-misses,dTLB-loads,iTLB-load-misses,iTLB-loads,L1-dcache-load-misses,L1-dcache-loads,L1-icache-load-misses,L1-icache-loads,raw-ldst-spec,raw-dp-spec,raw-ase-spec,raw-sve-inst-spec,raw-vfp-spec,raw-pc-write-spec,raw-br-pred,raw-op-spec),thermal_zone(1s)" -d 5s -s 100ms
python3 tracecat.py "parse:cpu_load,cpu_freq,cpu_idle,cpu_load2,cpu_freq2,cpu_freq_stat,cpu_freq_stat2,ddr_freq,ddr_freq_stat,gpu_freq,gpu_freq_stat,simpleperf,thermal_zone"

sleep 5

# Test 3
python3 tracecat.py "trace:cpu_load,cpu_freq,cpu_idle,cpu_load2(10ms),cpu_freq2,cpu_freq_stat,cpu_freq_stat2,ddr_freq(20ms),ddr_freq_stat,gpu_freq(30ms),gpu_freq_stat,simpleperf(com.android.systemui|branch-misses,bus-cycles,cache-misses,cache-references,cpu-cycles,instructions,stalled-cycles-backend,stalled-cycles-frontend,branch-load-misses,branch-loads,dTLB-load-misses,dTLB-loads,iTLB-load-misses,iTLB-loads,L1-dcache-load-misses,L1-dcache-loads,L1-icache-load-misses,L1-icache-loads,raw-ldst-spec,raw-dp-spec,raw-ase-spec,raw-sve-inst-spec,raw-vfp-spec,raw-pc-write-spec,raw-br-pred,raw-op-spec),thermal_zone(1,2,3)" -d 5s -s 1s
python3 tracecat.py "parse:cpu_load,cpu_freq,cpu_idle,cpu_load2,cpu_freq2,cpu_freq_stat,cpu_freq_stat2,ddr_freq,ddr_freq_stat,gpu_freq,gpu_freq_stat,simpleperf,thermal_zone"