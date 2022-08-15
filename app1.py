import dash                                
from dash import html
from dash import dcc
import pandas as pd
import plotly.express as px

df = pd.read_csv(r'https://raw.githubusercontent.com/mikejackson35/round4/main/stats.csv')
fig = px.scatter(df.loc[df.player_name=='Rahm, Jon'],
                    x = 'sg_app',
                    y = 'fin_text')

app = dash.Dash()
app.layout = html.Div([html.Div('Hello Golf Fans'),
             html.H1('H1 Tag Here'),
             html.Div(dcc.Dropdown(id='dropdown',options = [{'label':'A', 'value':'A'},{'label': 'B', 'value':'B'},{'lable': 'C', 'value':'C'}])),
             dcc.Graph(id='fig1',figure=fig)])
                                                                
app.run_server(debug=True)            
                                                                                                                                                                                                                         