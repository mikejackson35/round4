import dash                                
from dash import html
from dash import dcc
import pandas as pd
import plotly.express as px

df = pd.read_csv(f'https://github.com/mikejackson35/round4/blob/main/data/stats.csv')
fig = px.bar(df[df['player_name']=='Rahm, Jon'],
                    x = 'event_completed',
                    y = 'sg_app')

app = dash.Dash()
app.layout = html.Div([
    html.Div('Hello Golf Fans'),
    html.H1('H1 Tag Here'),
    # html.Div(dcc.Dropdown(id='dropdown',options = [
    #     {'label':'A', 'value':'A'},
    #     {'label': 'B', 'value':'B'},
    #     {'lable': 'C', 'value':'C'}])),
    dcc.Graph(id='fig1',figure=fig)])
                                                                
app.run_server(debug=True)            
                                                                                                                                                                                                                         