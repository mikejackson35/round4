import dash                                
from dash import html
from dash import dcc
import pandas as pd
import plotly.express as px
import numpy as np
import datetime as dt

stats = pd.read_csv(r'https://raw.githubusercontent.com/mikejackson35/round4/main/stats.csv')
data = pd.read_csv(r'https://raw.githubusercontent.com/mikejackson35/round4/main/data.csv')
dg_rankings = pd.read_csv(r'https://raw.githubusercontent.com/mikejackson35/round4/main/dg_rankings.csv')

################ CHART INPUTS #####################

stroke_delta = int(0)       # stroke_delta chose 0, 1, or 2
weeks_prior = int(36)       # weeks_prior chose any amount
weeks_after = int(4)        # weeks_after chose any amount
rank_bin = 'bin_100'        # rank_bin chose 'bin_40' or 'bin_100'
min_instances = int(1)      # min_instances chose any number > 0

###################################################

chart_data = data[data.r4_delta <= stroke_delta].reset_index(drop=True)

chart_data.event_completed = pd.to_datetime(chart_data.event_completed)
chart_data['prior_date'] = chart_data['event_completed'] - pd.Timedelta(weeks=weeks_prior)
chart_data['post_date'] = chart_data['event_completed'] + pd.Timedelta(weeks=weeks_after)

stats_cols = ['round_score','sg_putt', 'sg_arg', 'sg_app', 'sg_ott',
       'sg_t2g', 'sg_total', 'driving_dist', 'driving_acc', 'gir',
       'scrambling', 'prox_rgh', 'prox_fw']

########### loop thru data and grab stats for rounds before and after the tough loss ####################

losers_rounds = []

for i in np.arange(0, len(chart_data)):

    guy = chart_data.player_name[i]
    prior = str(chart_data.prior_date[i])
    event = str(chart_data.event_completed[i])
    post = str(chart_data.post_date[i])
    
    rounds_before = round(stats
                          [(stats.player_name == guy) & (stats.event_completed > prior) & (stats.event_completed < event)]
                          .groupby('player_name', as_index=False)
                          [stats_cols]
                          .mean(),2)
    
    rounds_after = round(stats
                         [(stats.player_name == guy) & (stats.event_completed < post) & (stats.event_completed > event)]
                         .groupby('player_name', as_index=False)
                         [stats_cols]
                         .mean(),2) 

    # add post_ prefix to columns headers
    rounds_after.columns = 'post_' + rounds_after.columns
    rounds_after.rename(columns={'post_player_name':'player_name'}, inplace=True)
    # merge players before and after rounds together and send to list
    all_rounds = pd.merge(rounds_before,rounds_after, on='player_name')
    losers_rounds.append(all_rounds)

# concat before and after rounds
custom_chart = pd.concat(losers_rounds).reset_index(drop=True)
######## end loop ############################################################################

# add datagolf rankings
temp_ranks = dg_rankings[['player_name','datagolf_rank']]
custom_chart = pd.merge(custom_chart, temp_ranks, on='player_name')
# add 'count'
temp_count = custom_chart.groupby('player_name',as_index=False)['sg_total'].count().sort_values('sg_total', ascending=False).rename(columns={'sg_total':'count'}).reset_index(drop=True)
custom_chart = custom_chart.merge(temp_count, on='player_name', how = 'left')
# add 'rank_bin'
temp_bin = chart_data[['player_name',rank_bin]].drop_duplicates()
custom_chart = custom_chart.merge(temp_bin, on='player_name', how = 'left')

# chose statistic and make final dataframe
temp_m = custom_chart.groupby('player_name',as_index=False)[['sg_total', 'post_sg_total']].mean()
custom_chart = custom_chart.merge(temp_m, on='player_name', how = 'left').rename(columns = 
                                                                                 {'sg_total_x':'sg_total_round', 
                                                                                  'sg_total_y':'sg_total', 
                                                                                  'post_sg_total_x':'post_sg_total_round',
                                                                                  'post_sg_total_y':'post_sg_total'}
                                                                                )
custom_chart['delta_sg_total'] = custom_chart['post_sg_total'] - custom_chart['sg_total']

# # title formatting
# def format_title(title, subtitle=None, subtitle_font_size=16):
#     title = f'<b>{title}</b>'
#     if not subtitle:
#         return title
#     subtitle = f'<span style="font-size: {subtitle_font_size}px;">{subtitle}</span>'
#     return f"{title} <b>{stroke_delta} or Less</b><br>Min Occurances: {min_instances}  /  {subtitle} {custom_chart[custom_chart['count'] >= min_instances]['delta_sg_total'].count()}  /  Player Count: {custom_chart[custom_chart['count'] >= min_instances]['player_name'].nunique()}<br>"

# # graph
# fig = px.scatter(round(custom_chart[
#     (custom_chart['count'] >= min_instances)# &
#     # ((custom_chart['delta_sg_total']>.99) | (custom_chart['delta_sg_total']<-.99))
#     ].sort_values(rank_bin),2),
#                  x = 'sg_total',
#                  y = 'post_sg_total',
#                  title = format_title('STROKES BACK:', "Sample Size:"),
#                  template = 'seaborn',
#                  color = rank_bin,
#                  size = 'count',
#                  size_max = 20,
#                  hover_name='player_name',
#                  custom_data=['player_name', 'count','datagolf_rank','delta_sg_total'],
#                  height = 700,
#                  width = 900,
#                 #  marginal_x='rug',
#                 #  marginal_y='rug'
#                 )

# # format grids and lines
# fig.add_hline(y=0,line_width=3, line_color="Black")
# fig.add_vline(x=0,line_width=3, line_color="Black")
# fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightPink')
# fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightPink')
# fig.add_shape(type="line", x0=-1.5, y0=-1.5, x1=2.5, y1=2.5, line=dict(color="DarkRed", width=1.5, dash="dashdot"))

# # format always-on labels
# fig.update_layout(xaxis_title=(f"SG/Rd - {str(weeks_prior)} WEEKS PRIOR"))
# fig.update_layout(yaxis_title=(f"SG/Rd - {str(weeks_after)} WEEKS AFTER"))
# fig.update_layout(yaxis = dict(titlefont = dict(size=15)))
# fig.update_layout(xaxis = dict(titlefont = dict(size=15)))
# fig.update_layout(legend_title="Datagolf Rank")

# # format hover labels
# fig.update_layout(hoverlabel=dict(font_size=15,font_family="Rockwell"))
# fig.update_traces(hovertemplate=
#                     "<b>%{customdata[0]}</b> \
#                     <br>Count: %{customdata[1]}</b> \
#                     <br>=================</b> \
#                     <br>SG Before:%{x:>20}<br>SG After:%{y:>23}</b> \
#                     <br><b>Change:%{customdata[3]:>23}</b> \
#                     <br>=================</b>") 
                    # <br>Wins Since 2017:%{customdata[4]:>10}</b> \
                    # <br>Data Golf Rank:%{customdata[2]:>13}")                  

#####  app   ###########################################################################################

# app = dash.Dash()
# app.layout = html.Div([#html.Div('Hello Golf Fans'),
#             #  html.H1('SG Before and After a Tough Loss'),
#             #  html.Div(dcc.Dropdown(id='dropdown',options = [{'label':min_instances_0, 'value':custom_chart['min_instances']},{'label':min_instances_1, 'value':custom_chart['min_instances']}])),
#             dcc.Graph(id='fig1',figure=fig)])
                                                                
# app.run_server(debug=True) 
# 
from flask import Flask, render_template
import json
import plotly          

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chart1')
def chart1():
    # title formatting
    def format_title(title, subtitle=None, subtitle_font_size=16):
        title = f'<b>{title}</b>'
        if not subtitle:
            return title
        subtitle = f'<span style="font-size: {subtitle_font_size}px;">{subtitle}</span>'
        return f"{title} <b>{stroke_delta} or Less</b><br>Min Occurances: {min_instances}  /  {subtitle} {custom_chart[custom_chart['count'] >= min_instances]['delta_sg_total'].count()}  /  Player Count: {custom_chart[custom_chart['count'] >= min_instances]['player_name'].nunique()}<br>"

        # graph
    fig = px.scatter(round(custom_chart
                        [(custom_chart['count'] >= min_instances) 
    #                         & (custom_chart['delta_sg_total']>.49) 
    #                         | (custom_chart['delta_sg_total']<-.49)
                        ]
                        .sort_values(rank_bin)
                        ,2),
                    x = 'sg_total',
                    y = 'post_sg_total',
                    title = format_title('STROKES BACK:', "Sample Size:"),
                    template = 'seaborn',
                    color_discrete_sequence=px.colors.qualitative.Antique,
                    color = 'bin_100',
                    size = 'count',
                    size_max = 20,
                    hover_name='player_name',
                    custom_data=['player_name', 'count','datagolf_rank','delta_sg_total','career_wins'],
                    height = 800,
                    width = 1000
                    )

    # format grids and lines
    fig.add_hline(y=0,line_width=3, line_color="Black")
    fig.add_vline(x=0,line_width=3, line_color="Black")
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightPink')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightPink')
    fig.add_shape(type="line", x0=-1.5, y0=-1.5, x1=2.5, y1=2.5, line=dict(color="DarkRed", width=1.5, dash="dashdot"))

    # format always-on labels
    fig.update_layout(xaxis_title=(f"SG/Rd - {str(weeks_prior)} WEEKS PRIOR"))
    fig.update_layout(yaxis_title=(f"SG/Rd - {str(weeks_after)} WEEKS AFTER"))
    fig.update_layout(yaxis = dict(titlefont = dict(size=15)))
    fig.update_layout(xaxis = dict(titlefont = dict(size=15)))
    fig.update_layout(legend_title="Datagolf Rank")

    # format hover labels
    fig.update_layout(hoverlabel=dict(font_size=15,font_family="Times New Roman"))

    fig.update_traces(hovertemplate=
                        "<b>%{customdata[0]}</b> \
                        <br>Count: %{customdata[1]}</b> \
                        <br>=================</b> \
                        <br>SG Before:%{x:>19}<br>SG After:%{y:>22}</b> \
                        <br><b>Change:%{customdata[3]:>23}</b>") 

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    header="Fruit in North America"
    description = """
    A academic study of the number of apples, oranges and bananas in the cities of
    San Francisco and Montreal would probably not come up with this chart.
    """
    return render_template('index.html', graphJSON=graphJSON, header=header,description=description)                                                                                                                                                                                    
