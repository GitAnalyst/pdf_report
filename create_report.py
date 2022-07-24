# %%
import pandas as pd
import numpy as np
import os
import glob
import json
from PyPDF2 import PdfFileMerger

import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import plotly.io as pio
#pio.kaleido.scope.mathjax = None # use this if mathjax appears on pdf files

# %% load settings from config
conf = json.load(open('config.json'))
report_name = conf['report_name']
# combined template and colours
template, set = conf['viz']['template'], conf['viz']['colours']
colours = getattr(px.colors.sequential,set)[::-1]
pio.templates[set] = go.layout.Template(layout=dict(colorway=colours))
pio.templates.default = f"{template}+{set}"

margin = conf['viz']['margin']

# %%
# %% clean any previous files before writing new ones
fileList = glob.glob('*.pdf')
for filePath in fileList:
    try:
        os.remove(filePath)
    except:
        print("Error while deleting file : ", filePath)


# %% load retail data from NY gov
# https://data.ny.gov/browse?category=Economic+Development&utf8=%E2%9C%93
# https://data.ny.gov/Economic-Development/Retail-Food-Stores/9a8c-vfzj/data
link = 'https://data.ny.gov/api/views/9a8c-vfzj/rows.csv?accessType=DOWNLOAD&sorting=true'
df_r = pd.read_csv(link)
df_r.shape


# %% load fips data from NY gov
link = "https://data.ny.gov/api/views/79vr-2kdi/rows.csv?accessType=DOWNLOAD&sorting=true"
fips = pd.read_csv(link)
county_fips = fips[['County Name', 'County FIPS']].drop_duplicates()

# %% merge retail data with fips data
df = df_r.merge(county_fips, left_on='County',
                right_on='County Name', how='left')
df.shape


# %%
# df['County'].value_counts()
t01 = df[df['Square Footage'] != 0].groupby(['County', 'County FIPS'], as_index=False).agg(
    avg_sqft=('Square Footage', 'mean')).sort_values(by='avg_sqft', ascending=False)

# %% Page 1: Map of Average Retail Sqft by County
values = t01['avg_sqft'].tolist()
fips = t01['County FIPS'].tolist()

endpts = list(np.mgrid[min(values):max(values):4j])
# colorscale = ["#030512", "#1d1d3b", "#323268", "#3d4b94", "#3e6ab0",
#               "#4989bc", "#60a7c7", "#85c5d3", "#b7e0e4", "#eafcfd"]
fig = ff.create_choropleth(
    fips=fips, values=values, scope=['NY'], show_state_data=True,
    colorscale=colours,
    binning_endpoints=endpts, round_legend_values=True,
    #plot_bgcolor='rgb(229,229,229)',
    #paper_bgcolor='rgb(229,229,229)',
    county_outline={'color': 'rgb(255,255,255)', 'width': 0.5},
    exponent_format=True
)

#fig.layout.template = None
fig.update_layout(margin=margin, title='Average Retail Square Footage By County Map')
fig.write_image('output/fig_01.pdf')
fig.show()

# %% Page 2: Average Retail Sqft by County
df

# %%
entity = 'DOLLAR TREE STORES INC'  # 'DOLGEN NEW YORK LLC'

df.loc[df['Entity Name'] == entity, 'DBA Name'].value_counts()


# %% Page 3: Most popular retail stores: by occurence and by
#df['Entity Name'].value_counts()
tsize = 4 # tick size

t03 = df.groupby([
    'Entity Name',
    #'DBA Name'
], as_index=False).agg(
    count=('County', 'count'),
    total_sqft=('Square Footage', 'sum')
).sort_values(by='count', ascending=True)
t03['text'] = t03['total_sqft'].map("{:,.0f}".format)

fig03a = px.bar(t03.tail(20), y='Entity Name', x='count', text='count')
fig03b = px.bar(t03.sort_values(by=['total_sqft']).tail(
    20), y='Entity Name', x='total_sqft', text='text')

fig03 = make_subplots(rows=2, cols=1, horizontal_spacing=0.2, vertical_spacing=0.1, subplot_titles=(
    'Store Count By Entity', 'Total Store Square Footage By Entity'))
fig03.add_trace(fig03a.data[0], row=1, col=1).add_trace(
    fig03b.data[0], row=2, col=1)
fig03.update_xaxes(tickfont=dict(size=tsize), row=1, col=1).update_xaxes(
    tickfont=dict(size=tsize), row=2, col=1)
fig03.update_yaxes(tickfont=dict(size=tsize), row=1, col=1).update_yaxes(
    tickfont=dict(size=tsize), row=2, col=1)
fig03.update_traces(textfont_size=tsize)
fig03.update_layout(margin=margin)
fig03.write_image('output/fig_03.pdf')
fig03

# %%


path = 'output/'
x = [path+a for a in os.listdir(path) if a.endswith(".pdf")]
#x = [x[0]]
merger = PdfFileMerger(strict=False)

for pdf in x:
    merger.append(open(pdf, 'rb'))

with open(f"report/{report_name}", "wb") as fout:
    merger.write(fout)

print('Saved: {report_name}')
# %%
