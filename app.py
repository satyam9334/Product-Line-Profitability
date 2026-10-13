import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. PAGE SETUP
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Nassau Candy Distributor | Profitability & Margin Dashboard",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. DATA PROCESSING & FACTORY ENRICHMENT
# -----------------------------------------------------------------------------
@st.cache_data
def load_and_preprocess_data():
    df = pd.read_csv("Nassau Candy Distributor.csv")
    
    # Clean & convert date columns
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y', errors='coerce')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], format='%d-%m-%Y', errors='coerce')
    
    # Calculate core KPIs
    df['Gross Margin %'] = (df['Gross Profit'] / df['Sales']) * 100
    df['Profit Per Unit'] = df['Gross Profit'] / df['Units']
    
    # Factory Correlation Map from Project Documentation
    factory_map = {
        "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
        "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
        "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
        "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
        "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
        "Laffy Taffy": "Sugar Shack",
        "SweeTARTS": "Sugar Shack",
        "Nerds": "Sugar Shack",
        "Fun Dip": "Sugar Shack",
        "Fizzy Lifting Drinks": "Sugar Shack",
        "Everlasting Gobstopper": "Secret Factory",
        "Lickable Wallpaper": "Secret Factory",
        "Wonka Gum": "Secret Factory",
        "Hair Toffee": "The Other Factory",
        "Kazookles": "The Other Factory"
    }
    
    # Factory Coordinates from Project Documentation
    factory_coords = {
        "Lot's O' Nuts": {"lat": 32.881893, "lon": -111.768036, "city": "Casa Grande, AZ"},
        "Wicked Choccy's": {"lat": 32.076176, "lon": -81.088371, "city": "Savannah, GA"},
        "Sugar Shack": {"lat": 48.119140, "lon": -96.181150, "city": "Thief River Falls, MN"},
        "Secret Factory": {"lat": 41.446333, "lon": -90.565487, "city": "Moline, IL"},
        "The Other Factory": {"lat": 35.117500, "lon": -89.971107, "city": "Memphis, TN"}
    }
    
    df['Factory'] = df['Product Name'].map(factory_map).fillna("Unknown")
    df['Factory Lat'] = df['Factory'].map(lambda f: factory_coords.get(f, {}).get('lat', None))
    df['Factory Lon'] = df['Factory'].map(lambda f: factory_coords.get(f, {}).get('lon', None))
    df['Factory Location'] = df['Factory'].map(lambda f: factory_coords.get(f, {}).get('city', 'Unknown'))
    
    return df

df_raw = load_and_preprocess_data()

# -----------------------------------------------------------------------------
# 3. SIDEBAR FILTERS (User Capabilities)
# -----------------------------------------------------------------------------
st.sidebar.title("🎛️ Dashboard Controls")

# Filter 1: Date Range Selector
min_date = df_raw['Order Date'].min().date()
max_date = df_raw['Order Date'].max().date()
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Filter 2: Division Filter
divisions_available = sorted(df_raw['Division'].dropna().unique().tolist())
selected_divisions = st.sidebar.multiselect(
    "Filter by Division",
    options=divisions_available,
    default=divisions_available
)

# Filter 3: Margin Threshold Slider (Margin Risk Flag)
margin_threshold = st.sidebar.slider(
    "Margin Risk Threshold (%)",
    min_value=0,
    max_value=100,
    value=25,
    help="Identifies product lines operating below this gross margin."
)

# Filter 4: Product Search
product_query = st.sidebar.text_input("🔍 Product Search", placeholder="e.g. Wonka, Kazookles...").strip().lower()

# Apply Filters
filtered_df = df_raw.copy()

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_d, end_d = date_range
    filtered_df = filtered_df[
        (filtered_df['Order Date'].dt.date >= start_d) &
        (filtered_df['Order Date'].dt.date <= end_d)
    ]

if selected_divisions:
    filtered_df = filtered_df[filtered_df['Division'].isin(selected_divisions)]

if product_query:
    filtered_df = filtered_df[filtered_df['Product Name'].str.lower().str.contains(product_query)]

# -----------------------------------------------------------------------------
# 4. TOP KPI SUMMARY METRICS
# -----------------------------------------------------------------------------
st.title("🍬 Nassau Candy Distributor")
st.subheader("Product Line Profitability & Margin Performance Intelligence")
st.markdown(
    "Live analytics evaluating product gross margins, cost diagnostics, "
    "operating division contributions, and portfolio dependency risks."
)

total_rev = filtered_df['Sales'].sum()
total_prof = filtered_df['Gross Profit'].sum()
total_cogs = filtered_df['Cost'].sum()
blended_margin = (total_prof / total_rev * 100) if total_rev > 0 else 0
total_volume = filtered_df['Units'].sum()

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Gross Revenue", f"${total_rev:,.2f}")
m2.metric("Gross Profit", f"${total_prof:,.2f}")
m3.metric("Blended Margin", f"{blended_margin:.1f}%")
m4.metric("Total Cost", f"${total_cogs:,.2f}")
m5.metric("Volume Sold", f"{total_volume:,} units")

st.divider()

# Prepare Product Summary for charts
prod_summary = filtered_df.groupby(['Product Name', 'Division', 'Factory']).agg(
    Revenue=('Sales', 'sum'),
    Cost=('Cost', 'sum'),
    Gross_Profit=('Gross Profit', 'sum'),
    Units=('Units', 'sum'),
    Orders=('Row ID', 'count')
).reset_index()

prod_summary['Gross Margin %'] = (prod_summary['Gross_Profit'] / prod_summary['Revenue']) * 100
prod_summary['Profit per Unit'] = prod_summary['Gross_Profit'] / prod_summary['Units']
prod_summary['Revenue Share %'] = (prod_summary['Revenue'] / total_rev * 100) if total_rev > 0 else 0
prod_summary['Profit Share %'] = (prod_summary['Gross_Profit'] / total_prof * 100) if total_prof > 0 else 0

# -----------------------------------------------------------------------------
# MODULE 1: PRODUCT PROFITABILITY OVERVIEW
# -----------------------------------------------------------------------------
st.header("1. Product Profitability Leaderboard & Contribution")
c1, c2 = st.columns([3, 2])

with c1:
    st.subheader("Product-Level Margin Leaderboard")
    sorted_prods = prod_summary.sort_values(by='Gross_Profit', ascending=True)
    fig_leaderboard = px.bar(
        sorted_prods,
        x='Gross_Profit',
        y='Product Name',
        color='Gross Margin %',
        orientation='h',
        color_continuous_scale='Mint',
        labels={'Gross_Profit': 'Gross Profit ($)', 'Product Name': ''},
        title="Gross Profit by Product Line (Color = Margin %)"
    )
    fig_leaderboard.update_layout(height=420, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_leaderboard, width="stretch")

with c2:
    st.subheader("Profit Contribution Breakdown")
    fig_contrib = px.pie(
        prod_summary,
        names='Product Name',
        values='Gross_Profit',
        hole=0.45,
        title="Share of Total Gross Profit"
    )
    fig_contrib.update_traces(textposition='inside', textinfo='percent+label')
    fig_contrib.update_layout(height=420, showlegend=False, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_contrib, width="stretch")

with st.expander("📊 View Detailed Product Economics Table"):
    st.dataframe(
        prod_summary.sort_values(by='Gross_Profit', ascending=False).style.format({
            'Revenue': '${:,.2f}', 'Cost': '${:,.2f}',
            'Gross_Profit': '${:,.2f}', 'Gross Margin \%': '{:.2f}\%', 'Profit per Unit': '${:,.2f}',
            'Revenue Share %': '{:.2f}%',
            'Profit Share %': '{:.2f}%',
            'Units': '{:,}',
            'Orders': '{:,}'
        }),
        width="stretch"
    )

st.divider()

# -----------------------------------------------------------------------------
# MODULE 2: DIVISION PERFORMANCE DASHBOARD
# -----------------------------------------------------------------------------
st.header("2. Division Performance Dashboard")
d1, d2 = st.columns(2)

div_summary = filtered_df.groupby('Division').agg(
    Revenue=('Sales', 'sum'),
    Gross_Profit=('Gross Profit', 'sum'),
    Cost=('Cost', 'sum')
).reset_index()

with d1:
    st.subheader("Revenue vs. Profit Comparison")
    div_melt = div_summary.melt(id_vars='Division', value_vars=['Revenue', 'Gross_Profit'],
                                var_name='Metric', value_name='Amount')
    fig_div = px.bar(
        div_melt,
        x='Division',
        y='Amount',
        color='Metric',
        barmode='group',
        color_discrete_map={'Revenue': '#2b5c8f', 'Gross_Profit': '#2e9d63'},
        title="Revenue vs. Profit Generated by Division"
    )
    fig_div.update_layout(height=380)
    st.plotly_chart(fig_div, width="stretch")

with d2:
    st.subheader("Margin Distribution by Division")
    fig_box = px.box(
        filtered_df,
        x='Division',
        y='Gross Margin %',
        color='Division',
        title="Order-Level Gross Margin Variance",
        points="outliers"
    )
    fig_box.update_layout(height=380)
    st.plotly_chart(fig_box, width="stretch")

st.divider()

# -----------------------------------------------------------------------------
# MODULE 3: COST VS. MARGIN DIAGNOSTICS & RISK FLAGS
# -----------------------------------------------------------------------------
st.header("3. Cost vs. Margin Diagnostics")
diag1, diag2 = st.columns([3, 2])

with diag1:
    st.subheader("Cost vs. Sales Scatter Diagnostics")
    fig_scatter = px.scatter(
        prod_summary,
        x='Cost',
        y='Revenue',
        size='Gross_Profit',
        color='Gross Margin %',
        hover_name='Product Name',
        color_continuous_scale='RdYlGn',
        title="Cost vs. Sales (Bubble Size: Profit, Color: Margin %)"
    )
    max_val = max(prod_summary['Cost'].max(), prod_summary['Revenue'].max()) if len(prod_summary) > 0 else 100
    fig_scatter.add_shape(
        type='line', line=dict(dash='dash', color='gray'),
        x0=0, y0=0, x1=max_val, y1=max_val
    )
    fig_scatter.update_layout(height=430)
    st.plotly_chart(fig_scatter, width="stretch")

with diag2:
    st.subheader(f"⚠️ Margin Risk Flags (< {margin_threshold}%)")
    risk_products = prod_summary[prod_summary['Gross Margin %'] < margin_threshold]
    
    if len(risk_products) > 0:
        st.warning(f"Found {len(risk_products)} product line(s) below your {margin_threshold}% target:")
        for _, row in risk_products.iterrows():
            st.error(
                f"**{row['Product Name']}** ({row['Division']})\n\n"
                f"* **Gross Margin:** `{row['Gross Margin %']:.2f}%`\n"
                f"* **Revenue:** `${row['Revenue']:,.2f}` | **Cost:** `${row['Cost']:,.2f}`\n"
                f"* **Total Profit:** `${row['Gross_Profit']:,.2f}`\n"
                f"* **Action:** Reprice list price or renegotiate supplier cost."
            )
    else:
        st.success(f"All active product lines meet or exceed the {margin_threshold}% hurdle rate.")

st.divider()

# -----------------------------------------------------------------------------
# MODULE 4: PROFIT CONCENTRATION & PARETO ANALYSIS
# -----------------------------------------------------------------------------
st.header("4. Profit Concentration Analysis (Pareto 80/20)")

pareto_df = prod_summary.sort_values(by='Gross_Profit', ascending=False).reset_index(drop=True)
pareto_df['Cumulative_Profit'] = pareto_df['Gross_Profit'].cumsum()
pareto_df['Cumulative_Profit_%'] = (pareto_df['Cumulative_Profit'] / total_prof) * 100 if total_prof > 0 else 0

fig_pareto = go.Figure()
fig_pareto.add_trace(go.Bar(
    x=pareto_df['Product Name'],
    y=pareto_df['Gross_Profit'],
    name='Product Profit ($)',
    marker_color='#4682B4'
))
fig_pareto.add_trace(go.Scatter(
    x=pareto_df['Product Name'],
    y=pareto_df['Cumulative_Profit_%'],
    name='Cumulative Profit %',
    yaxis='y2',
    mode='lines+markers',
    line=dict(color='#D9534F', width=3)
))
fig_pareto.add_hline(
    y=80, yref='y2', line_dash='dash', line_color='red',
    annotation_text='80% Threshold', annotation_position='bottom right'
)
fig_pareto.update_layout(
    title='Pareto Chart: Cumulative Gross Profit Contribution',
    yaxis=dict(title='Gross Profit ($)'),
    yaxis2=dict(
        title='Cumulative Profit %',
        overlaying='y',
        side='right',
        range=[0, 105]
    ),
    xaxis=dict(tickangle=-35),
    legend=dict(x=0.01, y=0.98),
    height=480
)
st.plotly_chart(fig_pareto, width="stretch")

top_3_pct = pareto_df.head(3)['Cumulative_Profit_%'].iloc[-1] if len(pareto_df) >= 3 else 0
st.info(
    f"🚨 **Dependency Indicator:** The top 3 products generate **{top_3_pct:.1f}%** of all corporate profits, "
    f"and the Chocolate division delivers **over 95%** of earnings. Nassau Candy faces severe single-category supply risk."
)

st.divider()

# -----------------------------------------------------------------------------
# MODULE 5: FACTORY SOURCING & GEOSPATIAL INTELLIGENCE
# -----------------------------------------------------------------------------
st.header("5. Factory Production & Sourcing Diagnostic")

factory_agg = filtered_df.groupby(['Factory', 'Factory Location', 'Factory Lat', 'Factory Lon']).agg(
    Produced_Sales=('Sales', 'sum'),
    Produced_Cost=('Cost', 'sum'),
    Produced_Profit=('Gross Profit', 'sum'),
    Total_Shipments=('Row ID', 'count')
).reset_index()

factory_agg['Factory Margin %'] = (factory_agg['Produced_Profit'] / factory_agg['Produced_Sales']) * 100

geo1, geo2 = st.columns([3, 2])

with geo1:
    st.subheader("Factory Footprint Map")
    fig_map = px.scatter_geo(
        factory_agg,
        lat='Factory Lat',
        lon='Factory Lon',
        size='Produced_Profit',
        color='Factory Margin %',
        hover_name='Factory',
        hover_data={'Factory Location': True, 'Produced_Sales': ':$,.2f', 'Factory Margin %': ':.1f%'},
        scope='usa',
        title="Manufacturing Hubs (Size: Profit, Color: Margin %)",
        color_continuous_scale='Viridis'
    )
    fig_map.update_layout(height=420, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_map, width="stretch")

with geo2:
    st.subheader("Factory Operational Matrix")
    st.dataframe(
        factory_agg[['Factory', 'Factory Location', 'Produced_Profit', 'Factory Margin %', 'Total_Shipments']].sort_values(
            by='Produced_Profit', ascending=False
        ).style.format({
            'Produced_Profit': '${:,.2f}',
            'Factory Margin %': '{:.2f}%',
            'Total_Shipments': '{:,}'
        }),
        width="stretch",
        height=380
    )