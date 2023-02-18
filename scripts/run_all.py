import os
import sys
import platform

if __name__ == '__main__':

    if len(sys.argv) <= 1:

        print('Tracecat batch parse or chart script.')

        print('Examples:')

        print('> run_all "parse:cpu_load,cpu_freq,cpu_freq_stat"')
        print('> run_all "chart:cpu_load,cpu_freq,cpu_freq_stat"')

        sys.exit()
    
    if getattr(sys, 'frozen', False):

        command = 'tracecat' if platform.system() == 'Windows' else './tracecat'

    else:
        command = 'python ./tracecat.py'

    runline = sys.argv[1]

    for file_name in os.listdir('./runs'):

        if os.path.isfile('./runs/' + file_name):

            continue

        if 'parse:' in runline:

            os.system('%s "%s" %s' % (command, runline, file_name))

        elif 'chart:' in runline:

            modules = runline.replace('chart:', '').split(',')

            for module in modules:

                os.system('%s "chart:%s" %s --export 1280,720' % (command, module, file_name))
        else:

            sys.exit('Error command format.')
