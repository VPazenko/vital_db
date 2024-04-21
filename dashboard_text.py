from bokeh.models.widgets import Div

def text_intro(variable):
    '''
    Return the text for the Dashboard pages
    '''
    text_box = ''
    if variable == 'Start':
        text_box = Div(text="<p>This Dashboard visually demonstrates the data collected during a patient operation. "
                       "Three vital parameters were taken as a dataset: ECG, heart rate and CO2 level of exhalation (breathing).</p>"
                       "<p>A Fourier transform based filter was also used (One of the variants proposed for the ECG "
                        'at <a href="https://cmi.to/%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7-%D1%8D%D0%BA%D0%B3/">Website</a> was implemented. '
                        "A high-pass filter). The signal input to the filter is possible as an array (in this case), but it is also possible"
                        " as a data stream (the result delay / offset is 100 values).</p>"
                        "<p>Peaks were found from the filtered signal (using the neurokit library). From these peaks was obtained the calculated heart rate values."
                        "On the 'Place of interest' page you can see details of three potentially dangerous areas: near the 'Operation start', 'Operation end' and 'Anestesia end'.</p>"
                        "<p>On the 'Free analysis' page you can choose your own interval.</p>"
                        "<p>On the '(Pseudo)Streaming' page you can choose your own interval, preferred update rate (number of values) and x-axis resolution " 
                        "(number of values / 500 = number of seconds).</p>", styles={'font-size': '16px'})
 
    elif variable == 'operation start':
        text_box = Div(text="As we can see, just before and immediately after the start of the operation, the patient had irregularly cardiac rhythm (highlighted on the graph).<br \>"
                       "Also, at some moments, the calculated heart rate was above normal (above 100 bpm). Respiration was normal.", styles={'font-size': '16px'})

    elif variable == 'operation end':
        text_box = Div(text="As we can see, just before and immediately after the end of the operation, the patient had irregularly cardiac rhythm (highlighted on the graph) and "
                       "the calculated heart rate (strong fluctuations, sometimes above 100 bpm). Respiration was normal.", styles={'font-size': '16px'})
        
    elif variable == 'anestesia end':
        text_box = Div(text="As we can see, before the end of the anestesia, the patient had irregularly cardiac rhythm (highlighted on the graph). "
                       "The calculated pulse rate came close to the critical value of 100 bpm, and after some time crossed this border. "
                       "The respiratory pattern was no longer normal. Distortions are noticeable.", styles={'font-size': '16px'})
    
    elif variable == 'valueble changes':
        text_box = Div(text="This graph shows the dynamics of the parameters after about 2.5 minutes after the anaesthesia was stopped. "
                       "As can be noticed, the patient had irregularly cardiac rhythm (highlighted on the graph). The calculated pulse rate "
                       "above the critical value of 100 bpm for most of the time interval. Respiration was irregular, interrupted. "
                       "The respiratory pattern was no more normal.", styles={'font-size': '16px'})

    return text_box