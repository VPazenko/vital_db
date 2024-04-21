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
    '''
    Input: 

    Function return a df with Time, ECG, co2 and Hr parameters

    Output: df_class - dataframe placed in the class
    '''    
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

    # Data contain millions of values, so using np.array() - fastest way
    df = pd.DataFrame(np.array([time_ecg, ecg])).T
    df.rename(columns = {0:'Time', 1:'ECG'}, inplace = True )
    df2 = pd.DataFrame(np.array([time_co2, co2])).T
    df2.rename(columns = {0:'Time', 1:'co2'}, inplace = True )
    df3 = pd.DataFrame(np.array([time_hr, hr])).T
    df3.rename(columns = {0:'Time', 1:'Hr'}, inplace = True )
    df = df.merge(df2, on='Time', how='outer')
    df = df.merge(df3, on='Time', how='outer')

    # Put raw data in the class
    df_class = classes.Data_store(df)
    return df_class
    

def data_transformation(Data_store, start=0, stop=10000):
    '''
    Input: 1. Data_store - element with type class and contain all raw info

    Function return a final df with all data and list of peaks indexes

    Output: 1. df_final - df with all data including transformed ECG and calculated Hr
            2. list_of_peaks_index - list of peaks indexes
    '''    
    ecg_f = Data_store.fourier_transform(np.array(Data_store.raw_data.loc[:,'ECG'])[start:stop])

    df_ecg_f = pd.DataFrame(np.array([np.array(Data_store.raw_data.loc[:,'Time'])[start:stop], ecg_f])).T
    df_ecg_f.rename(columns = {0:'Time', 1:'ECG_f'}, inplace = True )
    df_final = Data_store.raw_data.merge(df_ecg_f, on='Time', how='outer')
    df_p, list_of_peaks_index = Data_store.find_peaks_and_hr(df_final[start:stop])
    df_final = df_final.merge(df_p.iloc[:,[1,6,7]], on='Time', how='outer')

    return df_final, list_of_peaks_index


def graph_plotting(df_graph, places_dict=None, start=0, stop=10000, place=None):
    '''
    Input: 1. df_graph - df with raw data
           2. places_dict - dictionary with different events/time 
           3. start - start index in dataframe == time in seconds * 500
           4. stop - stop index in dataframe == time in seconds * 500
           5. place - name of the event from places_dict

    Function return a plot (1 - graph with Hr and co2, 2 - ECG, ECG transformed, 3 - range tool)

    Output: plot
    '''   
    place_time = 0

    # Just add one more event that not connect with lab_names
    if place == 'valueble changes':
        start = 7207000
        stop = 7240000
    # Use values from dictionary
    elif places_dict:
        start = places_dict[place] - 10000
        stop = places_dict[place] + 10000
        place_time = (stop + start)//2//500

    # Find final df
    df, peaks_filter = data_transformation(df_graph, start=start, stop=stop)

    # Find df with peaks for highlighting
    df_circle = df[start:stop].iloc[peaks_filter]
    df_circle = df_circle.loc[df_circle.loc[:,'ECG_f'] < 0.4]

    # Create filter for peaks
    view = CDSView(filter=IndexFilter(peaks_filter))
    # Create Datasources
    source_ecg = ColumnDataSource(df[start:stop])
    source_co2 = ColumnDataSource(df[start:stop].dropna(subset=['co2']))
    source_hr = ColumnDataSource(df[start:stop].dropna(subset=['Hr']))
    source_hr_count = ColumnDataSource(df[start:stop].dropna(subset=['hr']))

    # Create figure 1 and add layouts
    p = figure(height=400, width=1000, 
            background_fill_color="#efefef", x_range=(df.loc[:,'Time'][start], df.loc[:,'Time'][stop]), y_range=(-0.5, 2))

    p.line('Time', 'ECG', source=source_ecg, color='green', legend_label='Original ECG')
    p.line('Time', 'ECG_f', source=source_ecg, color='red', legend_label='Fourier ECG')
    p.yaxis.axis_label = 'ECG signal'
    p.xaxis.axis_label = 'Time, s'
    p.scatter('Time', 'ECG_f', size=5, color='red',  hover_color="black", source=source_ecg, view=view)
    p.circle(x=df_circle['Time'], y=df_circle['ECG_f'], line_color='black', size=70, fill_alpha=0)
    
    # Add vertical line and label if place_time is active
    if place_time:
        p.vspan(x=place_time, line_width=[3], line_color="blue")
        label = Label(x=place_time, y=1.5, x_units='data', y_units='data', text=' ' + place + ' ',
                    x_offset=5,
            border_line_color='black', border_line_alpha=1.0)
        p.add_layout(label)

    # Create figure 2 and add layouts
    p2 = figure(height=400, width=1000, 
            background_fill_color="#efefef", x_range=p.x_range, y_range=(-5, df.loc[:,'hr'].max()+5))

    p2.line('Time', 'co2', source=source_co2, color = "blue", legend_label='co2 level (breathing)')
    p2.line('Time', 'Hr', source=source_hr, color = "black", legend_label='Hr level (detected)')
    p2.line('Time', 'hr', source=source_hr_count, color = "red", legend_label='Hr level (calculated)')
    p2.yaxis.axis_label = 'Hr signal / co2 signal'
    p2.xaxis.axis_label = 'Time, s'
    p2.hspan(y=100, line_width=[3], line_color="black")

    # Add vertical line and label if place_time is active
    if place_time:
        p2.vspan(x=place_time, line_width=[3], line_color="blue")
        label = Label(x=place_time, y=80, x_units='data', y_units='data', text=' ' + place + ' ',
                    x_offset=5,
            border_line_color='black', border_line_alpha=1.0)
        p2.add_layout(label)

    # Create range tool
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



def give_values_for_streaming(df_class, start, stop):
    """ 
    Input: 1. df_class - dataframe placed in the class
           3. start - start index in dataframe == time in seconds * 500
           4. stop - stop index in dataframe == time in seconds * 500

    Function, kind of, combination between data_transformation() and first steps of the graph_plotting()

    Output: df_final - df with all data + interpolate for 'NaN' values (for the streaming)
    """
    ecg_f = df_class.fourier_transform(np.array(df_class.raw_data.loc[start:stop,'ECG']))
    df_ecg_f = pd.DataFrame(np.array([np.array(df_class.raw_data.loc[start:stop,'Time']), ecg_f])).T
    df_ecg_f.rename(columns = {0:'Time', 1:'ECG_f'}, inplace = True )
    new_df = df_class.raw_data.merge(df_ecg_f, on='Time', how='outer')

    df_p, list_of_peaks_index = df_class.find_peaks_and_hr(new_df)
    df_final = new_df.merge(df_p.iloc[:,[1,6,7]], on='Time', how='outer')
    df_final.iloc[:,[2,3,6]] = df_final.iloc[:,[2,3,6]] .interpolate(method='linear', axis=0)
    df_final.loc[:, 'error peaks'] = np.where((df_final.loc[:, 'peaks'] == 1.0)&(df_final.loc[:, 'ECG_f'] < 0.4), df_final.loc[:, 'ECG_f'], np.nan)
    
    return df_final


def graph_plotting_streaming(source):
    '''
    Input: 1. source - ColumnDataSource dictionary with all datas for these graphs

    Function return a plot (1 - graph with Hr and co2, 2 - ECG, ECG transformed)

    Output: plot
    '''   

    # Create figure 1 and add layouts
    p = figure(height=400, width=1000, 
            background_fill_color="#efefef", y_range=(-0.5, 2)) 

    # ECG line
    p.line('Time', 'ECG', source=source, color='green', legend_label='Original ECG')
    # ECG transformed line
    p.line('Time', 'ECG_f', source=source, color='red', legend_label='Fourier ECG')
    
    p.yaxis.axis_label = 'ECG signal'
    p.xaxis.axis_label = 'Time, s'
    
    # ECG transformed dots
    p.scatter('Time', 'ECG_f', size=5, color='red',  hover_color="black", source=source) 
    # Big circles for the filtered peaks (too low values for the peaks)
    p.circle('Time', 'error peaks', source=source, line_color='black', size=70, fill_alpha=0)

    # Create figure 2 and add layouts
    p2 = figure(height=400, width=1000, background_fill_color="#efefef", x_range=p.x_range)  

    # co2 line
    p2.line('Time', 'co2', source=source, color = "blue", legend_label='co2 level (breathing)')
    # Hr line
    p2.line('Time', 'Hr', source=source, color = "black", legend_label='Hr level (detected)')
    # Hr calculated line
    p2.line('Time', 'hr', source=source, color = "red", legend_label='Hr level (calculated)')
    
    p2.yaxis.axis_label = 'Hr signal / co2 signal'
    p2.xaxis.axis_label = 'Time, s'
    
    # Limitation line (Hr > 100 bpm is dangerous)
    p2.hspan(y=100, line_width=[3], line_color="black")

    return (column(p2, p))



if __name__ == "__main__":
    print(__doc__)
else:
    print(f"Module '{__name__}' is imported successfully!\n")