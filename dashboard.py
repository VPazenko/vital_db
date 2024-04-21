# Imports
import module
import dashboard_text
import panel as pn
from bokeh.models import RangeSlider, Slider, ColumnDataSource


import time
df_class = module.give_me_df_with_parameters()

# Create a dictionary with different events/time 
config = module.open_config_yaml('config\config.yaml')
operation_events = {'operation start': config['time_opstart']*500, 'operation end': config['time_opend']*500, 
                    'anestesia end': config['time_anestend']*500, 'case end': config['time_caseend']*500}

pn.extension(sizing_mode="stretch_width")

# selection widget
places = pn.widgets.Select(options=['operation start', 'operation end', 'anestesia end', 'valueble changes'], sizing_mode='stretch_both')

# Create buttons
home_button = pn.widgets.Button(name='Home', button_type='light', align='start', width=175)
place_of_interest_button = pn.widgets.Button(name='Place of interest', button_type='light', align='start', width=175)
free_analysis_button = pn.widgets.Button(name='Free analysis', button_type='light', align='start', width=175)
slider_button = pn.widgets.Button(name='Ok', button_type='light', align='start', width=50)
streaming_button = pn.widgets.Button(name='(Pseudo)Streaming', button_type='light', align='start', width=175)
start_stream_button = pn.widgets.Button(name='Start', button_type='light', align='start', width=80)

# Create sliders
range_slider = RangeSlider(start=2, end=config['time_caseend'], value=(1020, 2000), step=1, title="Select the interval of interest")
speed_slider = Slider(start=1, end=50, value=5, step=1., title="Streaming speed")
x_range_slider = Slider(start=500, end=5000, value=2000, step=50., title="Number of points (x range/500, s)")

def dashboard():
    #home_page = pn.pane.HTML('<h1>Welcome to the Home Page!</h1>')

    dashboard_column = pn.Column()
    sidebar_column = pn.Column()

    # Bind graph function and text with select widget
    graph = pn.bind(module.graph_plotting, df_graph = df_class, places_dict=operation_events, place=places)
    text = pn.bind(dashboard_text.text_intro, variable=places)

    template = pn.template.FastListTemplate(
        title='Some key parameters of patient #0367 during surgery.',
        sidebar=[home_button, place_of_interest_button, free_analysis_button, streaming_button, pn.layout.Divider(), pn.Spacer(height=25)],
        sidebar_width=200,
        accent='#144A50')

    # Append the sidebar and dashboard columns to the template
    template.sidebar.append(sidebar_column)
    template.main.append(dashboard_column)

    # Define the dashboard title
    home_page_title = pn.Row(pn.pane.HTML('<h1>Welcome to the dashboard</h1>'))
    
    # Append the home_page to the dashboard layout that will show when the dashboard is executed
    dashboard_column.append(home_page_title)
    dashboard_column.append(pn.Column(pn.Spacer(height=50), dashboard_text.text_intro(variable='Start')))

    def home_click(event):
        # Clear the sidebar and dashboard layout
        dashboard_column.clear()
        sidebar_column.clear()

        # Add the contents to the dashboard layout
        dashboard_column.append(home_page_title)
        dashboard_column.append(pn.Column(pn.Spacer(height=50), dashboard_text.text_intro(variable='Start')))

    def free_analysis_click(event):
        # Clear the sidebar and dashboard layout
        dashboard_column.clear()
        sidebar_column.clear()

        # Add the contents to the dashboard layout
        dashboard_column.append(range_slider)
        dashboard_column.append(pn.Spacer(height=25))
        dashboard_column.append(slider_button)
    
    def place_of_interest_click(event):
        # Clear the sidebar and dashboard layout
        dashboard_column.clear()
        sidebar_column.clear()

        # Add the contents to the sidebar layout
        sidebar_column.append(pn.pane.HTML('<b>Select the place of interest to see details:</b>'))
        sidebar_column.append(places)

        # Add the contents to the dashboard layout
        dashboard_column.append(pn.Row(graph, text))

    def streaming_click(event):
        # Clear the sidebar and dashboard layout
        dashboard_column.clear()
        sidebar_column.clear()

        # Add the contents to the dashboard layout
        dashboard_column.append(pn.Column(range_slider, pn.Spacer(height=15), speed_slider, pn.Spacer(height=15), x_range_slider))
        dashboard_column.append(pn.Spacer(height=30))
        dashboard_column.append(start_stream_button)
        dashboard_column.append(pn.Spacer(height=30))


    def slider_click(event):
        # read the slider value
        a = range_slider.value

        # Add the contents to the dashboard layout
        dashboard_column.append(pn.pane.HTML('<b>Please wait. If the gap is too long, it may takes time.</b>'))
        graph2 = module.graph_plotting(df_graph = df_class, start=int(a[0])*500, stop=int(a[1])*500)
        dashboard_column.append(pn.Spacer(height=25))
        dashboard_column.append(graph2)


    def start_click(event):
        # read the slider values
        range_s = range_slider.value
        speed = speed_slider.value
        x_range = x_range_slider.value
        # Clear old plot (if exist)
        streaming_click(event=1)
        
        # Calculate start and stop indexes
        start=int(range_s[0])*500
        stop=int(range_s[1])*500

        # Add the contents to the dashboard layout
        dashboard_column.append(pn.pane.HTML('<b>Please wait. Preprocessing in progress. It may takes time.</b>'))

        # Define source and draw a graph
        df_final = module.give_values_for_streaming(df_class, start-200, stop)
        source = ColumnDataSource(df_final[start-100:start])
        new_graph = module.graph_plotting_streaming(source)
        dashboard_column.append(new_graph)

        # start data transfer to the graph with the speed of 'speed' values.
        for i in range(start, stop, speed):
            new_start = i
            new_stop = i + speed 
            
            # Add new data. IF number of datapoints became large then 'rollover', function rewrite old values
            source.stream({'ECG': df_final.loc[new_start:new_stop, 'ECG'], 'Time': df_final.loc[new_start:new_stop, 'Time'], 'ECG_f': df_final.loc[new_start:new_stop,
                            'ECG_f'], 'index': df_final.loc[new_start:new_stop, 'peaks'], 'Hr': df_final.loc[new_start:new_stop, 'Hr'], 
                            'co2': df_final.loc[new_start:new_stop, 'co2'], 'hr': df_final.loc[new_start:new_stop, 'hr'], 'peaks': df_final.loc[new_start:new_stop, 'peaks'],
                            'error peaks': df_final.loc[new_start:new_stop, 'error peaks']}, rollover=x_range)

    # Execute the click functions when the user clicks on a button
    home_button.on_click(home_click)
    free_analysis_button.on_click(free_analysis_click)
    place_of_interest_button.on_click(place_of_interest_click)
    streaming_button.on_click(streaming_click)
    slider_button.on_click(slider_click)
    start_stream_button.on_click(start_click)

    return template

pn.serve({"/": dashboard})