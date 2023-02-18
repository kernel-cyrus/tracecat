import pandas

from abc import ABC, abstractmethod

class Plotter():

    def __init__(self):
        
        self.kwargs = dict()

    def init_plot(self, **kwargs):

        self.kwargs = kwargs

    # This function parameters are the same as pandas df.plot
    def plot(self, df, name = None, **kwargs):

        kwargs.update(self.kwargs)

        df.plot(**kwargs).set_ylabel(name)

    def plot_index_chart(self, params, df, name, index, x, y, **kwargs):

        if df.dtypes[index] == 'int64':

            index_type = int
        else:
            index_type = str

        index_list = params if params else sorted(df[index].unique().tolist())

        for idx in index_list:

            self.plot(df[df[index] == index_type(idx)], name, x=x, y=y, label=y + '_' + str(idx), **kwargs)

    def plot_paral_chart(self, params, df, name, x, y_prefixer, **kwargs):

        if not params:

            self.plot(df, name, x=x, y=[col for col in df.columns.values if y_prefixer in col], **kwargs)
        
        else:

            for param in params:

                if '-' in param:

                    args = param.split('-')

                    ids = range(int(args[0]), int(args[1]))

                    df_mean = pandas.DataFrame()

                    df_mean[x] = df[x]

                    df_mean[y_prefixer + param] = df[[y_prefixer + str(i) for i in ids]].mean(axis=1)

                    self.plot(df_mean, name, x=x, y=[y_prefixer + param], **kwargs)

                else:

                    self.plot(df, name, x=x, y=[y_prefixer + param], **kwargs)