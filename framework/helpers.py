import sys
import pandas
import os.path
import datetime

def get_element(array, index, default = None):

    return array[index] if len(array) > index else default

def get_slices(records, start_time, end_time = None, duration = None):

    slices = list()

    for row in records:

        new = {
            'start_time': int(row[start_time]),
            'end_time':   int(row[end_time]) if end_time else 0,
            'duration':   int(row[duration]) if duration else 0
        }

        if not new['end_time'] and not new['duration']:

            raise Exception('end_time and duration cannot be both None.')

        if not end_time:
            new['end_time'] = new['start_time'] + new['duration']
        
        if not duration:
            new['duration'] = new['end_time'] - new['start_time']
        
        slices.append(new)

    return slices

def sub_slices(slices, start_time, end_time):

    subset = list()

    for idx, row in enumerate(slices):

        if row['end_time'] <= start_time:
            continue

        if row['start_time'] >= end_time:
            break

        new = row.copy()

        if row['start_time'] < start_time:
            new['start_time'] = start_time
            new['duration']   = new['end_time'] - new['start_time']

        if row['end_time'] > end_time:
            new['end_time'] = end_time
            new['duration'] = new['end_time'] - new['start_time']

        subset.append(new)

    return subset

def get_slices_usage(slices, start_time, end_time):

    up_time = sum([s['duration'] for s in slices])

    return up_time / (end_time - start_time)

def get_time(time_str, time_unit, check_format = True):

    time_ms = 0

    if 'ms' in time_str:

        time_ms = int(time_str.replace('ms', ''))

    elif 's' in time_str:

        time_ms = int(time_str.replace('s', '')) * 1000

    else:

        if check_format:

            sys.exit('ERROR: Invalid time format, please use 1ms, 1s.')

        else:

            return int(time_str)

    if time_unit == 'ms':

        return time_ms

    elif time_unit == 's':

        return time_ms / 1000

    else:

        raise Exception('Invalide time unit, only support s, ms.')

def pick_next_window(window, start_time, end_time, window_time, ignore_broken_window = False):

    window_id = 0 if not window else window['id'] + 1

    next_window = {
        'id': window_id,
        'start': start_time + window_id * window_time,
        'end':   start_time + window_id * window_time + window_time,
        'dur':   window_time,
        'broken': False
    }

    if next_window['start'] >= end_time:

        return None

    if next_window['end'] > end_time:

        if ignore_broken_window:

            return None

        next_window['end'] = end_time
        next_window['dur'] = next_window['end'] - next_window['start']
        next_window['broken'] = True

    return next_window

def get_unique_list(df, cols, skip_none = False):

    results = list()

    df_comb = pandas.DataFrame()

    for col_name, col_type in cols.items():

        df_comb['combine'] = (df_comb['combine'] if 'combine' in df_comb else '') + df[col_name].astype(str) + '\t'

    unique_list = df_comb['combine'].dropna().unique().tolist()

    for row in unique_list:

        has_none = False

        argx = 0

        args = row.split('\t')

        data = dict()

        for col_name, col_type in cols.items():

            if args[argx] == 'None':

                has_none = True

            data[col_name] = col_type(args[argx]) if args[argx] != 'None' else None # FIXME: It's a temporery fix None value.

            argx += 1

        if skip_none and has_none:

            continue

        results.append(data)

    return results

def get_runtime_path():

    return getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)) + '/../')

def create_seq_list(extra, prefix, ids):

    if type(extra) == str:

        extra = [extra]

    return extra + [prefix + str(i) for i in ids]

def create_seq_dict(extra, prefix, ids, data_type):

    result = dict()

    if type(extra) == str:

        extra = [extra]

    for attr in extra:

        result[attr] = data_type()

    for i in ids:

        result[prefix + str(i)] = data_type()

    return result

def create_duration_column(df, end_time = None, ts_col = 'timestamp', dur_col = 'duration'):

    next_df = df[ts_col].shift(-1)

    if end_time:

        next_df.iloc[-1] = end_time

    df[dur_col] = next_df - df[ts_col]

    return df

def log_current_command(log_file):
    
    now = datetime.datetime.now()

    with open(log_file, 'a') as log_file:
        
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")

        cmd_line = ' '.join(sys.argv)

        log_file.write("%s: %s\n" % (time_str, cmd_line, ))

def handle_thread_exceptions(thread_func):

    def wrapper(*args):

        try:
            thread_func(*args)
        except SystemExit as e: 
            print(e)
        except:
            traceback.print_exc()

    return wrapper

g_ftrace_taker = None

def take_ftrace_buffer(taker):

    global g_ftrace_taker

    if g_ftrace_taker and g_ftrace_taker != taker:

        sys.exit('ERROR: Can\'t enable %s because ftrace buffer is taken by %s, please remove the conflict modules and try again.' % (taker, g_ftrace_taker))
        
    g_ftrace_taker = taker