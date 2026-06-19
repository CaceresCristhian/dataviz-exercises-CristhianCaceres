import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="CO2 Dashboard", page_icon="🌱", layout="wide")

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
        border: 1px solid rgba(16, 185, 129, 0.25);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Title and headers */
    h1 {
        font-weight: 700 !important;
        background: linear-gradient(135deg, #065F46 0%, #10B981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem !important;
    }
    
    h2, h3 {
        font-weight: 600 !important;
        color: #1F2937 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    path = Path(__file__).parent.parent / 'data' / 'co2_emissions.csv'
    df = pd.read_csv(path)
    df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-01-01')
    return df

df = load_data()

st.title("🌱 CO2 Emissions Explorer")
st.caption("Source: Our World in Data — ourworldindata.org/co2-emissions")

# ── TASK 1: Sidebar with 5 widgets ────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    
    # a) st.selectbox for Region (with 'All')
    regions = ['All'] + sorted(df['Region'].unique().tolist())
    selected_region = st.selectbox("Region", regions)
    
    # b) st.multiselect for Countries (chained to selected region)
    if selected_region == 'All':
        country_options = sorted(df['Country'].unique().tolist())
    else:
        country_options = sorted(df[df['Region'] == selected_region]['Country'].unique().tolist())
    
    selected_countries = st.multiselect(
        "Countries", 
        country_options, 
        default=country_options[:min(3, len(country_options))]
    )
    
    # c) st.date_input for date range (two-handle; convert years to Jan-1 dates)
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    selected_dates = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Guards
    if not selected_countries:
        st.warning("Please select at least one country.")
        st.stop()
        
    if not isinstance(selected_dates, (tuple, list)) or len(selected_dates) < 2:
        st.warning("Please select both start and end dates.")
        st.stop()
        
    start_date = pd.Timestamp(selected_dates[0])
    end_date = pd.Timestamp(selected_dates[1])
    
    st.divider()
    
    # d) st.radio for Metric
    metric = st.radio("Metric", ["Total CO2 (Mt)", "CO2 per capita"])
    
    # e) st.checkbox for highlighting top emitter
    highlight_top = st.checkbox("Show only top emitter highlighted")

# Apply all filters
filtered = df[
    df['Country'].isin(selected_countries) &
    (df['Date'] >= start_date) &
    (df['Date'] <= end_date)
]

# Set up column names and labels based on metric
y_col = 'CO2_Mt' if metric == "Total CO2 (Mt)" else 'CO2_per_capita'
y_label = 'CO2 Emissions (Mt)' if y_col == 'CO2_Mt' else 'CO2 per Capita (t)'

# ── TASK 2: Filter summary caption ────────────────────────────────────────────
num_countries = len(selected_countries)
region_str = selected_region
dates_str = f"{start_date.year}–{end_date.year}"
st.caption(f"{num_countries} countries | Region: {region_str} | {dates_str} | Metric: {metric} | {len(filtered)} records match filters")

# ── EXTENSION: KPI row above the charts ───────────────────────────────────────
if not filtered.empty:
    last_year = filtered['Year'].max()
    first_year = filtered['Year'].min()
    
    latest_year_data = filtered[filtered['Year'] == last_year]
    first_year_data = filtered[filtered['Year'] == first_year]
    
    if not latest_year_data.empty and not first_year_data.empty:
        # Metric 1: Total/Avg in last year
        if metric == "Total CO2 (Mt)":
            val_last = latest_year_data[y_col].sum()
            val_first = first_year_data[y_col].sum()
            kpi1_value = f"{val_last:,.1f} Mt"
            kpi1_label = f"Total CO2 Emissions ({last_year})"
        else:
            val_last = latest_year_data[y_col].mean()
            val_first = first_year_data[y_col].mean()
            kpi1_value = f"{val_last:.2f} t"
            kpi1_label = f"Avg CO2 per Capita ({last_year})"
            
        # Metric 2: % change
        pct_change = ((val_last - val_first) / val_first * 100) if val_first != 0 else 0
        
        # Metric 3: Top emitter in last year
        top_row = latest_year_data.loc[latest_year_data[y_col].idxmax()]
        top_country = top_row['Country']
        top_value = top_row[y_col]
        kpi3_value = top_country
        kpi3_delta = f"{top_value:,.1f} Mt" if metric == "Total CO2 (Mt)" else f"{top_value:.2f} t"
        
        st.write("") # small spacer
        kcol1, kcol2, kcol3 = st.columns(3)
        kcol1.metric(kpi1_label, kpi1_value)
        kcol2.metric(f"% Change ({first_year}–{last_year})", f"{pct_change:+.1f}%", delta=f"{pct_change:+.1f}%", delta_color="inverse")
        kcol3.metric(f"Top Emitter ({last_year})", kpi3_value, delta=kpi3_delta, delta_color="off")
        st.divider()

# ── TASK 3: Two charts reacting to ALL filters ────────────────────────────────
col_left, col_right = st.columns([2, 1])

# Identify top emitter overall in the selected date range
if not filtered.empty:
    top_emitter = filtered.groupby('Country')[y_col].max().idxmax()
else:
    top_emitter = None

with col_left:
    if not filtered.empty:
        # BBD colour type: highlight (if checked) else categorical
        if highlight_top and top_emitter:
            fig1 = px.line(
                filtered, x='Year', y=y_col, color='Country',
                labels={y_col: y_label},
                title=f"📈 {metric} Over Time: {top_emitter} is the Leading Emitter"
            )
            # Customizing trace style for SWD highlight
            for trace in fig1.data:
                if trace.name == top_emitter:
                    trace.line.color = '#065F46'  # Deep emerald highlight
                    trace.line.width = 4
                else:
                    trace.line.color = '#E5E7EB'  # Neutralized gray
                    trace.line.width = 1.5
            fig1.update_layout(showlegend=False)
            
            # Label country at the end of its line
            top_emitter_data = filtered[filtered['Country'] == top_emitter]
            if not top_emitter_data.empty:
                last_row = top_emitter_data.loc[top_emitter_data['Year'].idxmax()]
                fig1.add_annotation(
                    x=last_row['Year'],
                    y=last_row[y_col],
                    text=f"  {top_emitter}",
                    showarrow=False,
                    xanchor="left",
                    yanchor="middle",
                    font=dict(color="#065F46", size=12, weight="bold")
                )
                # Expand x-axis range slightly to prevent label clipping
                min_year = filtered['Year'].min()
                max_year = filtered['Year'].max()
                fig1.update_layout(xaxis=dict(range=[min_year, max_year + (max_year - min_year) * 0.15]))
        else:
            fig1 = px.line(
                filtered, x='Year', y=y_col, color='Country',
                color_discrete_sequence=px.colors.qualitative.Safe,
                labels={y_col: y_label},
                title=f"📈 {metric} Over Time by Country"
            )
            
        fig1.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Arial', size=12),
            xaxis=dict(gridcolor='#F3F4F6', showgrid=True),
            yaxis=dict(gridcolor='#F3F4F6', showgrid=True),
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig1, width='stretch')

with col_right:
    if not filtered.empty:
        last_year = filtered['Year'].max()
        latest = filtered[filtered['Year'] == last_year].sort_values(y_col, ascending=True)
        
        # BBD colour type: highlight (if checked) else sequential
        if highlight_top and top_emitter:
            fig2 = px.bar(
                latest, x=y_col, y='Country', orientation='h',
                color='Country',
                color_discrete_map={c: '#065F46' if c == top_emitter else '#E5E7EB' for c in latest['Country']},
                labels={y_col: y_label, 'Country': ''},
                title=f"📊 {top_emitter} Leads in {last_year}"
            )
            fig2.update_layout(showlegend=False)
        else:
            fig2 = px.bar(
                latest, x=y_col, y='Country', orientation='h',
                color=y_col,
                color_continuous_scale='Greens',
                labels={y_col: y_label, 'Country': ''},
                title=f"📊 Country Rankings in {last_year}"
            )
            fig2.update_layout(coloraxis_showscale=False)
            
        fig2.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(family='Arial', size=12),
            xaxis=dict(gridcolor='#F3F4F6', showgrid=True, range=[0, latest[y_col].max() * 1.15]),
            yaxis=dict(showgrid=False),
            margin=dict(l=10, r=10, t=30, b=10)
        )
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(fig2, width='stretch')