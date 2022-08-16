import dash                                
from dash import html
from dash import dcc
import pandas as pd
import plotly.express as px
import numpy as np
import datetime as dt

file_one_df = pd.read_csv(r'https://raw.githubusercontent.com/mikejackson35/round4/main/stats.csv')
file_three_df = pd.read_csv(r'https://raw.githubusercontent.com/mikejackson35/round4/main/dg_rankings.csv')

# cleanup 'finish_pos'
stats = file_one_df.copy()
stats['fin_text'] = pd.to_numeric(stats['fin_text'].str.replace("T",""), errors='coerce')
stats.rename(columns={'fin_text':"finish_pos"}, inplace=True) 

# make unique event identifier just in case it becomes handy later (concat year and event_id)
# add score to par column
stats['unique_event_id'] = stats['season'].astype(str) + stats['event_id'].astype(str)
stats['score_to_par'] = stats['round_score'] - stats['course_par']
stats.drop(stats[stats.round_score < 40].index, inplace=True)

# add player world rankings, current datagolf rankings, and skill estimate
dg_rankings = file_three_df.copy()
temp_ranks = dg_rankings[['player_name', 'owgr_rank', 'datagolf_rank', 'dg_skill_estimate']]
stats = pd.merge(stats, temp_ranks, on='player_name')

non_stat_cols = ['event_name','unique_event_id','event_completed','player_name','round_num','round_score','finish_pos','datagolf_rank']

# leaderboard thru 3 rounds of all tournaments
temp = stats[(stats.round_num < 4) & (stats.season > 2017)][non_stat_cols].sort_values(['event_completed','player_name','round_num','round_score'])
temp['cum_sum'] = temp.groupby(['player_name','unique_event_id'])['round_score'].cumsum(axis=0)
leaderboard_after_3 = temp[temp.round_num==3].sort_values(['unique_event_id', 'cum_sum']) # keeping for leaderboard thru 3 rounds

# # r4_delta column 
temp = leaderboard_after_3.groupby('unique_event_id')[['unique_event_id','cum_sum']].min().rename(columns={'cum_sum':'cum_sum_min'}).reset_index(drop=True)
leaderboard_deltas_after_3 = pd.merge(leaderboard_after_3,temp,on='unique_event_id')
leaderboard_deltas_after_3['r4_delta'] = leaderboard_deltas_after_3.cum_sum - leaderboard_deltas_after_3.cum_sum_min

# data golf rankings bins by 100
bins100 = [0, 100, 200, 300, 400, 500]
labels100 = ['1-100', '101-200', '201-300', '301-400', '401-500']
bins40 = [0, 40, 80, 120, 160, 200, 240, 280, 320, 360, 400, 440, 500]
labels40 = ['1-40', '41-80', '81-120', '121-160', '161-200', 
            '201-240', '241-280', '281-320', '321-360', '361-400', 
            '400-440', '441-500']
stats['bin_40'] = pd.cut(stats['datagolf_rank'], bins=bins40, labels=labels40)
stats['bin_100'] = pd.cut(stats['datagolf_rank'], bins=bins100, labels=labels100)
leaderboard_deltas_after_3['bin_100'] = pd.cut(leaderboard_deltas_after_3['datagolf_rank'], bins=bins100, labels=labels100)
leaderboard_deltas_after_3['bin_40'] = pd.cut(leaderboard_deltas_after_3['datagolf_rank'], bins=bins40, labels=labels40)

# remove winners, whittle down to 2 strokes delta maximum
losers_df = leaderboard_deltas_after_3[(leaderboard_deltas_after_3.r4_delta <= 2) & (leaderboard_deltas_after_3.finish_pos > 1)].reset_index(drop=True)

# # remove now un-needed columns and fix dtypes
losers_df.drop(columns=['round_score','round_num','cum_sum','cum_sum_min'], axis=1, inplace=True)
losers_df.event_completed = pd.to_datetime(losers_df.event_completed)
losers_df.finish_pos = losers_df.finish_pos.astype('int64')
stats.event_completed = pd.to_datetime(stats.event_completed)

data = losers_df.copy() # the 554 instances where a player was leading or within 2 strokes going into round 4 and lost

# CHART INPUTS ##############################################

stroke_delta = int(0)       # stroke_delta chose 0, 1, or 2
weeks_prior = int(24)       # weeks_prior chose any amount
weeks_after = int(6)        # weeks_after chose any amount
rank_bin = 'bin_100'        # rank_bin chose 'bin_40' or 'bin_100'
min_instances = int(2)      # min_instances chose any number > 0

#############################################################

chart_data = data[data.r4_delta <= stroke_delta].reset_index(drop=True)

chart_data['prior_date'] = chart_data['event_completed'] - pd.Timedelta(weeks=weeks_prior)
chart_data['post_date'] = chart_data['event_completed'] + pd.Timedelta(weeks=weeks_after)

stats_cols = ['round_score','sg_putt', 'sg_arg', 'sg_app', 'sg_ott',
       'sg_t2g', 'sg_total', 'driving_dist', 'driving_acc', 'gir',
       'scrambling', 'prox_rgh', 'prox_fw']

#######

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
    
########

# concat before and after rounds
custom_chart = pd.concat(losers_rounds).reset_index(drop=True)

# add datagolf rankings columns
temp_ranks = dg_rankings[['player_name','datagolf_rank']]
custom_chart = pd.merge(custom_chart, temp_ranks, on='player_name')

# bring in 'count', wins, and 'datagolf_rank', and 'rank_bin'
temp_count = custom_chart.groupby('player_name',as_index=False)['sg_total'].count().sort_values('sg_total', ascending=False).rename(columns={'sg_total':'count'}).reset_index(drop=True)
custom_chart = custom_chart.merge(temp_count, on='player_name', how = 'left')
temp_bin = chart_data[['player_name',rank_bin]].drop_duplicates()
custom_chart = custom_chart.merge(temp_bin, on='player_name', how = 'left')
temp_wins = stats[(stats.finish_pos == 1) & (stats.round_num == 4)].groupby('player_name')['finish_pos'].count().sort_values(ascending=False)
custom_chart = custom_chart.merge(temp_wins, on='player_name', how = 'left')
custom_chart.rename(columns={'finish_pos':'career_wins'},inplace=True)
custom_chart['career_wins'] = custom_chart['career_wins'].fillna(0)

# chose statistic and make final dataframe
temp_m = custom_chart.groupby('player_name',as_index=False)[['sg_total', 'post_sg_total']].mean()
custom_chart = custom_chart.merge(temp_m, on='player_name', how = 'left').rename(columns = 
                                                                                 {'sg_total_x':'sg_total_round', 
                                                                                  'sg_total_y':'sg_total', 
                                                                                  'post_sg_total_x':'post_sg_total_round',
                                                                                  'post_sg_total_y':'post_sg_total'}
                                                                                )
custom_chart['delta_sg_total'] = custom_chart['post_sg_total'] - custom_chart['sg_total']

# title formatting
def format_title(title, subtitle=None, subtitle_font_size=16):
    title = f'<b>{title}</b>'
    if not subtitle:
        return title
    subtitle = f'<span style="font-size: {subtitle_font_size}px;">{subtitle}</span>'
    return f"{title} <b>{stroke_delta} or Less</b><br>Min Occurances: {min_instances}  /  {subtitle} {custom_chart[custom_chart['count'] >= min_instances]['delta_sg_total'].count()}  /  Player Count: {custom_chart[custom_chart['count'] >= min_instances]['player_name'].nunique()}<br>"

# graph
fig = px.scatter(round(custom_chart[
    (custom_chart['count'] >= min_instances)# & 
    # ((custom_chart['delta_sg_total']>.24) | (custom_chart['delta_sg_total']<-.24))
    ].sort_values(rank_bin),2),
                 x = 'sg_total',
                 y = 'post_sg_total',
                 title = format_title('STROKES BACK:', "Sample Size:"),
                 template = 'seaborn',
                 color = rank_bin,
                 size = 'count',
                 size_max = 20,
                 hover_name='player_name',
                 custom_data=['player_name', 'count','datagolf_rank','delta_sg_total','career_wins'],
                 height = 750,
                 width = 900
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
fig.update_layout(hoverlabel=dict(font_size=15,font_family="Rockwell"))
fig.update_traces(hovertemplate=
                    "<b>%{customdata[0]}</b> \
                    <br>Count: %{customdata[1]}</b> \
                    <br>=================</b> \
                    <br>SG Before:%{x:>20}<br>SG After:%{y:>23}</b> \
                    <br><b>Change:%{customdata[3]:>23}</b> \
                    <br>=================</b> \
                    <br>Wins Since 2017:%{customdata[4]:>10}</b> \
                    <br>Data Golf Rank:%{customdata[2]:>13}")

###################################################################################################

app = dash.Dash()
app.layout = html.Div([#html.Div('Hello Golf Fans'),
            #  html.H1('SG Before and After a Tough Loss'),
            #  html.Div(dcc.Dropdown(id='dropdown',options = [{'label':'A', 'value':'A'},{'label': 'B', 'value':'B'},{'lable': 'C', 'value':'C'}])),
             dcc.Graph(id='fig1',figure=fig)])
                                                                
app.run_server(debug=True)            
                                                                                                                                                                                                                         