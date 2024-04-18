import vitaldb
import numpy as np
import pandas as pd
import yaml
from bokeh.models import CDSView, ColumnDataSource, IndexFilter
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, RangeTool
from bokeh.plotting import figure
from bokeh.models import Label

import classes

def open_config_yaml(directory):
    '''
    Input: 1. directory - config.yaml file

    Function return a dictionary from directory file

    Output: dictionary from (config file)
    '''
    with open(directory, 'r') as config_info:
        config_dict = yaml.safe_load(config_info)
    return config_dict


def give_me_df_with_parameters():

    # We can also download interesting data and import values manually, but I suppose using an api for this is easier
    ecg_val = vitaldb.load_case(367, ['SNUADC/ECG_II','SNUADC/ECG_V5'], 1/500)
    hr_val = vitaldb.load_case(367,'Solar8000/HR', 2)
    co2_val = vitaldb.load_case(367, 'Primus/CO2', 1/62.5)
    ecg = ecg_val[:,0]
    co2 = co2_val[:,0]
    hr = hr_val[:,0]

    #remove all outliers
    ecg = ecg*((ecg>-0.4)&(ecg<1.4))

    #Create time for every point
    time_ecg = np.arange(0, len(ecg), 1) / 500
    time_co2 = np.arange(0, len(co2), 1) / 62.5
    time_hr = np.arange(0, len(hr), 1) * 2


    df = pd.DataFrame(np.array([time_ecg, ecg])).T
    df.rename(columns = {0:'Time', 1:'ECG'}, inplace = True )
    df2 = pd.DataFrame(np.array([time_co2, co2])).T
    df2.rename(columns = {0:'Time', 1:'co2'}, inplace = True )
    df3 = pd.DataFrame(np.array([time_hr, hr])).T
    df3.rename(columns = {0:'Time', 1:'Hr'}, inplace = True )

    df = df.merge(df2, on='Time', how='outer')
    df = df.merge(df3, on='Time', how='outer')
    df_class = classes.Data_store(df)
    return df_class
    

def data_transformation(Data_store, start=0, stop=10000):
    
    ecg_f = Data_store.fourier_transform(np.array(Data_store.raw_data.loc[:,'ECG'])[start:stop])

    df_ecg_f = pd.DataFrame(np.array([np.array(Data_store.raw_data.loc[:,'Time'])[start:stop], ecg_f])).T
    df_ecg_f.rename(columns = {0:'Time', 1:'ECG_f'}, inplace = True )
    df_final = Data_store.raw_data.merge(df_ecg_f, on='Time', how='outer')
    df_p, list_of_peaks_index = Data_store.find_peaks_and_hr(df_final[start:stop])
    df_final = df_final.merge(df_p.iloc[:,[1,6,7]], on='Time', how='outer')

    return df_final, list_of_peaks_index


def graph_plotting(df_graph, places_dict=None, start=0, stop=10000, place=None):
    place_time = 0

    if place == 'valueble changes':
        start = 7207000
        stop = 14480*500
    elif places_dict:
        start = places_dict[place] - 10000
        stop = places_dict[place] + 10000
        place_time = (stop + start)//2//500

    df, peaks_filter = data_transformation(df_graph, start=start, stop=stop)

    df_circle = df[start:stop].iloc[peaks_filter]
    df_circle = df_circle.loc[df_circle.loc[:,'ECG_f'] < 0.4]

    view = CDSView(filter=IndexFilter(peaks_filter))
    source_ecg = ColumnDataSource(df[start:stop])
    source_co2 = ColumnDataSource(df[start:stop].dropna(subset=['co2']))
    source_hr = ColumnDataSource(df[start:stop].dropna(subset=['Hr']))
    source_hr_count = ColumnDataSource(df[start:stop].dropna(subset=['hr']))
    p = figure(height=400, width=1000, 
            background_fill_color="#efefef", x_range=(df.loc[:,'Time'][start], df.loc[:,'Time'][stop]), y_range=(-0.5, 2))

    p.line('Time', 'ECG', source=source_ecg, color='green', legend_label='Original ECG')
    p.line('Time', 'ECG_f', source=source_ecg, color='red', legend_label='Fourier ECG')
    p.yaxis.axis_label = 'ECG signal'
    p.xaxis.axis_label = 'Time, s'
    p.scatter('Time', 'ECG_f', size=5, color='red',  hover_color="black", source=source_ecg, view=view)
    p.circle(x=df_circle['Time'], y=df_circle['ECG_f'], line_color='black', size=70, fill_alpha=0)

    if place_time:
        p.vspan(x=place_time, line_width=[3], line_color="blue")
        label = Label(x=place_time, y=1.5, x_units='data', y_units='data', text=' ' + place + ' ',
                    x_offset=5,
            border_line_color='black', border_line_alpha=1.0)
        p.add_layout(label)

    p2 = figure(height=400, width=1000, 
            background_fill_color="#efefef", x_range=p.x_range, y_range=(-5, df.loc[:,'hr'].max()+5))

    p2.line('Time', 'co2', source=source_co2, color = "blue", legend_label='co2 level (breathing)')
    p2.line('Time', 'Hr', source=source_hr, color = "black", legend_label='Hr level (detected)')
    p2.line('Time', 'hr', source=source_hr_count, color = "red", legend_label='Hr level (calculated)')
    p2.yaxis.axis_label = 'Hr signal / co2 signal'
    p2.xaxis.axis_label = 'Time, s'
    p2.hspan(y=100, line_width=[3], line_color="black")
    if place_time:
        p2.vspan(x=place_time, line_width=[3], line_color="blue")
        label = Label(x=place_time, y=80, x_units='data', y_units='data', text=' ' + place + ' ',
                    x_offset=5,
            border_line_color='black', border_line_alpha=1.0)
        p2.add_layout(label)

    select = figure(title="Drag the middle and edges of the selection box to change the range above",
                    height=150, width=1000,    y_range=p.y_range,
                    tools="", toolbar_location=None, background_fill_color="#efefef")

    range_tool = RangeTool(x_range=p.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2

    select.line('Time', 'ECG', source=source_ecg)
    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)
    select.toolbar.active_multi = 'auto'

    return(column(p2, p, select))

