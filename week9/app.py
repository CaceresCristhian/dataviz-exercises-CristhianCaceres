import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="World Happiness Dashboard", page_icon="🌍", layout="wide")

# Inject premium CSS styling (custom fonts, glassmorphism metric cards, and clean styling)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Main container and font */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* Premium Glassmorphism KPI Card styling */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.6);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.06);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.4);
        padding: 20px 24px;
        transition: all 0.3s ease-in-out;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.12);
        border: 1px solid rgba(46, 117, 182, 0.25);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Title and headers */
    h1 {
        font-weight: 700 !important;
        background: linear-gradient(135deg, #1E3A8A 0%, #2E75B6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem !important;
    }
    
    h2, h3 {
        font-weight: 600 !important;
        color: #1E293B !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Data Loading ─────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / 'data'
try:
    df = pd.read_csv(DATA_DIR / 'world_happiness_2023.csv')
except FileNotFoundError:
    # Fallback to local path if run from a different directory
    df = pd.read_csv('../data/world_happiness_2023.csv')

df.columns = ['Country', 'Region', 'Score', 'GDP', 'Social_Support',
              'Life_Expectancy', 'Freedom', 'Generosity', 'Corruption']

global_mean_score = df['Score'].mean()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    regions = ['All'] + sorted(df['Region'].unique().tolist())
    selected_region = st.selectbox("Region", regions)
    top_n = st.slider("Show top N countries", 5, 30, 15)

# ── Filtered Data ─────────────────────────────────────────────────────────────
filtered = df if selected_region == 'All' else df[df['Region'] == selected_region]
top = filtered.nlargest(top_n, 'Score').sort_values('Score')

# ── Title Block ───────────────────────────────────────────────────────────────
st.title("🌍 World Happiness Dashboard")
st.caption("Source: World Happiness Report 2023 | Kaggle")

# ── KPI Cards Row ─────────────────────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
k1.metric(
    label="Countries in Selection", 
    value=len(filtered)
)
k2.metric(
    label="Avg Happiness Score", 
    value=f"{filtered['Score'].mean():.2f}",
    delta=f"{filtered['Score'].mean() - global_mean_score:+.2f} vs global avg ({global_mean_score:.2f})"
)
k3.metric(
    label="Happiest in Selection",
    value=filtered.nlargest(1, 'Score')['Country'].values[0],
    delta=f"Score: {filtered['Score'].max():.2f}"
)

st.divider()

# ── Row 1: Rankings (Sequential) + Scatter (Highlight) ─────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Happiness Rankings")
    # sequential colour scale — ordered bars going from light to dark
    fig1 = px.bar(
        top, x='Score', y='Country', orientation='h',
        color='Score',
        color_continuous_scale='Blues',
        range_color=[4.5, 8.5],
        labels={'Score': 'Happiness Score (0–10)', 'Country': ''},
    )
    fig1.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(range=[0, 8.5], gridcolor='#EEEEEE'),
        yaxis=dict(showgrid=False),
        coloraxis_showscale=False,
        font=dict(family='Arial', size=12),
        margin=dict(l=10, r=10, t=5, b=10),
    )
    fig1.update_traces(marker_line_width=0)
    st.plotly_chart(fig1, use_container_width=True)

with col_right:
    st.subheader("Score vs GDP")
    # highlight colour scale — single clean blue to highlight the trend
    fig2 = px.scatter(
        filtered, x='GDP', y='Score', hover_name='Country',
        color_discrete_sequence=['#2E75B6'],
        labels={'GDP': 'Log GDP per Capita', 'Score': 'Happiness Score'},
    )
    fig2.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(gridcolor='#EEEEEE'),
        yaxis=dict(gridcolor='#EEEEEE'),
        font=dict(family='Arial', size=12),
        margin=dict(l=10, r=10, t=5, b=10),
    )
    fig2.update_traces(marker=dict(size=9, opacity=0.8))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Row 2: Diverging Chart (Class Exercise) ───────────────────────────────────
st.subheader("Difference from Global Average Happiness Score")
st.markdown(
    f"This diverging chart highlights how much each country in the selection is happier or unhappier "
    f"than the global average of **{global_mean_score:.2f}**. "
    f"Blue indicates scores above average, and red indicates scores below average."
)

# Prepare diverging data
filtered_dev = filtered.copy()
filtered_dev['Score_Dev'] = filtered_dev['Score'] - global_mean_score
# Sort from unhappiest to happiest so the bars progress cleanly
filtered_dev = filtered_dev.sort_values('Score_Dev', ascending=True)

# Diverging color scale: Red/Orange for negative, light gray for midpoint, Blue for positive
diverging_colors = ['#E63946', '#F8FAFC', '#2E75B6']

fig3 = px.bar(
    filtered_dev,
    x='Score_Dev',
    y='Country',
    orientation='h',
    color='Score_Dev',
    color_continuous_scale=diverging_colors,
    color_continuous_midpoint=0.0,
    labels={'Score_Dev': 'Deviation from Average', 'Country': ''},
)

# Dynamic height to look perfect depending on count of countries
chart_height = max(350, 150 + 18 * len(filtered_dev))

fig3.update_layout(
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(family='Arial', size=12),
    xaxis=dict(
        gridcolor='#EEEEEE',
        title="Difference from Global Avg Happiness Score",
        zeroline=True,
        zerolinecolor='#7F7F7F',
        zerolinewidth=1.5
    ),
    yaxis=dict(showgrid=False),
    coloraxis_showscale=True,
    coloraxis_colorbar=dict(
        title="Deviation",
        tickvals=[-2, -1, 0, 1, 2],
        ticktext=["-2.00 (Unhappier)", "-1.00", "0.00 (Average)", "+1.00", "+2.00 (Happier)"],
        len=0.8,
        y=0.5
    ),
    margin=dict(l=10, r=10, t=30, b=10),
    height=chart_height
)

fig3.update_traces(marker_line_width=0)

# Add dashed line at midpoint (0.0)
fig3.add_vline(x=0.0, line_dash="dash", line_color="#7F7F7F", line_width=1.5)

# Label the midpoint (0.0) in an annotation positioned cleanly at the top of the line
fig3.add_annotation(
    x=0.0,
    y=1.02,
    yref='paper',
    text="Global Average (5.81)",
    showarrow=False,
    font=dict(family='Arial', size=11, color='#475569', weight='bold'),
    bgcolor="#FFFFFF",
    bordercolor="#CBD5E1",
    borderwidth=1,
    borderpad=5,
    align="center"
)

st.plotly_chart(fig3, use_container_width=True)

st.divider()
st.caption("Built with Streamlit + Plotly | Class Exercise Solution")
