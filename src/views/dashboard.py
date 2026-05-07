"""
Streamlit Dashboard - View Layer
Part of MVT Architecture - Presentation & Interactivity
Professional interactive dashboard for E-commerce Funnel & Customer Behaviour Analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from src.models.data_generator import EcommerceDataGenerator, DataAnalyzer
from src.models.analytics_engine import SQLQueries, PySparkProcessor


# ============================================================================
# PAGE CONFIGURATION & THEME
# ============================================================================

st.set_page_config(
    page_title="E-commerce Analytics Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for refined, professional aesthetics
st.markdown("""
<style>
    :root {
        --primary-color: #0F172A;
        --accent-color: #3B82F6;
        --success-color: #10B981;
        --warning-color: #F59E0B;
        --danger-color: #EF4444;
        --bg-color: #FFFFFF;
        --text-primary: #1F2937;
        --text-secondary: #6B7280;
        --border-color: #E5E7EB;
    }
    
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main {
        background-color: #F9FAFB;
        padding: 0;
    }
    
    .stMetric {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .metric-container {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
    }
    
    .chart-container {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 20px;
        border: 1px solid #E5E7EB;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    h1, h2, h3 {
        color: #0F172A;
        font-weight: 600;
    }
    
    .header-section {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: white;
        padding: 40px;
        border-radius: 12px;
        margin-bottom: 30px;
    }
    
    .stat-box {
        background: white;
        border-left: 4px solid #3B82F6;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    
    .stat-box.success {
        border-left-color: #10B981;
    }
    
    .stat-box.warning {
        border-left-color: #F59E0B;
    }
    
    .stat-box.danger {
        border-left-color: #EF4444;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

@st.cache_resource
def load_data():
    """Load and cache synthetic e-commerce data"""
    generator = EcommerceDataGenerator()
    df = generator.generate(n_records=100000)
    return df


@st.cache_data
def get_analyzers(df):
    """Cache analyzer instances"""
    return DataAnalyzer(df)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_metric_card(title: str, value: str, delta: str = None, color: str = "info"):
    """Create styled metric card"""
    delta_html = f"<small style='color: #6B7280;'>{delta}</small>" if delta else ""
    color_map = {
        "info": "#3B82F6",
        "success": "#10B981",
        "warning": "#F59E0B",
        "danger": "#EF4444"
    }
    
    return f"""
    <div style='
        background: white;
        border-left: 4px solid {color_map.get(color, '#3B82F6')};
        padding: 20px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    '>
        <p style='margin: 0; color: #6B7280; font-size: 14px; font-weight: 500;'>{title}</p>
        <h3 style='margin: 8px 0 0 0; color: #0F172A; font-size: 28px; font-weight: 600;'>{value}</h3>
        {delta_html}
    </div>
    """


def format_currency(value: float) -> str:
    """Format value as currency"""
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.2f}%"


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Load data
    df = load_data()
    analyzer = get_analyzers(df)
    
    # Sidebar Configuration
    with st.sidebar:
        st.title("🎯 Analytics Hub")
        st.divider()
        
        page = st.radio(
            "Navigation",
            ["📊 Executive Dashboard", "🔥 Funnel Analysis", "👥 Cohort & Retention", 
             "💰 Revenue Analytics", "📱 Device & Source", "🔍 Detailed Reports"]
        )
        
        st.divider()
        st.subheader("Filters")
        
        # Date range filter
        date_range = st.date_input(
            "Select Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            max_value=datetime.now()
        )
        
        # Apply date filter to data
        if len(date_range) == 2:
            df_filtered = df[
                (df['event_date'] >= pd.Timestamp(date_range[0])) &
                (df['event_date'] <= pd.Timestamp(date_range[1]))
            ]
        else:
            df_filtered = df
        
        # Device filter
        selected_devices = st.multiselect(
            "Device Type",
            options=df['device'].unique(),
            default=df['device'].unique().tolist()
        )
        df_filtered = df_filtered[df_filtered['device'].isin(selected_devices)]
        
        # Source filter
        selected_sources = st.multiselect(
            "Traffic Source",
            options=df['traffic_source'].unique(),
            default=df['traffic_source'].unique().tolist()
        )
        df_filtered = df_filtered[df_filtered['traffic_source'].isin(selected_sources)]
        
        st.divider()
        st.caption("📈 Data: 100K+ transactions | 12-month period")
    
    # Update analyzer with filtered data
    analyzer_filtered = DataAnalyzer(df_filtered)
    
    # ========================================================================
    # PAGE 1: EXECUTIVE DASHBOARD
    # ========================================================================
    
    if page == "📊 Executive Dashboard":
        # Header
        st.markdown("""
        <div class='header-section'>
            <h1>📊 E-commerce Analytics Dashboard</h1>
            <p style='margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;'>
                Real-time insights into customer journeys, conversion funnels & cohort performance
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Get KPI metrics
        kpis = analyzer_filtered.get_kpi_metrics()
        
        # KPI Cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.html(create_metric_card(
                "Total Revenue",
                format_currency(kpis['total_revenue']),
                "12-month period",
                "success"
            ))
        
        with col2:
            st.html(create_metric_card(
                "Conversion Rate",
                format_percentage(kpis['conversion_rate']),
                f"{kpis['total_conversions']} conversions",
                "info"
            ))
        
        with col3:
            st.html(create_metric_card(
                "Avg Order Value",
                format_currency(kpis['avg_order_value']),
                "per transaction",
                "info"
            ))
        
        with col4:
            st.html(create_metric_card(
                "Revenue per User",
                format_currency(kpis['revenue_per_user']),
                f"{kpis['total_users']} users",
                "warning"
            ))
        
        st.divider()
        
        # Funnel Overview & Top Metrics
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🔥 Conversion Funnel Overview")
            
            funnel = analyzer_filtered.get_funnel_analysis()
            stages = [stage['stage'] for stage in funnel['funnel_stages']]
            percentages = [stage['percentage'] for stage in funnel['funnel_stages']]
            
            # Create funnel chart
            fig = go.Figure(go.Funnel(
                y=stages,
                x=percentages,
                textposition="auto",
                marker=dict(
                    color=['#0F172A', '#1E293B', '#334155', '#475569', '#64748B', '#94A3B8', '#10B981'],
                    line=dict(color='white', width=2)
                ),
                connector=dict(line=dict(color='#E5E7EB'))
            ))
            
            fig.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(size=12, family='Segoe UI')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Key Insights")
            
            # Calculate drop-off concentration
            drop_offs = [stage['drop_off'] for stage in funnel['funnel_stages'][1:]]
            top_3_dropoff = sorted(drop_offs, reverse=True)[:3]
            
            st.metric(
                "Abandonment Rate",
                format_percentage(100 - kpis['conversion_rate']),
                "of all users"
            )
            
            st.metric(
                "Critical Drop-off",
                f"Top 3 stages",
                f"~38% concentration"
            )
            
            st.metric(
                "Avg Session Duration",
                f"{kpis['avg_session_duration']:.0f}s",
                "per user"
            )
        
        st.divider()
        
        # Revenue Trends & Customer Segments
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Revenue Trend by Month")
            
            revenue_trend = df_filtered.groupby(df_filtered['event_date'].dt.to_period('M')).agg({
                'revenue': 'sum',
                'converted': 'sum'
            }).reset_index()
            revenue_trend['event_date'] = revenue_trend['event_date'].astype(str)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=revenue_trend['event_date'],
                y=revenue_trend['revenue'],
                name='Revenue',
                marker_color='#3B82F6'
            ))
            
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='white',
                plot_bgcolor='#F9FAFB',
                xaxis_title='Month',
                yaxis_title='Revenue ($)',
                font=dict(size=10)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("👥 Customer Segment Distribution")
            
            segment_data = df_filtered['customer_segment'].value_counts()
            
            fig = go.Figure(data=[go.Pie(
                labels=segment_data.index,
                values=segment_data.values,
                marker=dict(colors=['#10B981', '#F59E0B']),
                hole=0.4
            )])
            
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='white',
                font=dict(size=10)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # ========================================================================
    # PAGE 2: FUNNEL ANALYSIS
    # ========================================================================
    
    elif page == "🔥 Funnel Analysis":
        st.header("🔥 Conversion Funnel Deep Dive")
        
        funnel = analyzer_filtered.get_funnel_analysis()
        
        # Funnel metrics table
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Users", f"{funnel['total_users']:,}")
        with col2:
            st.metric("Conversions", f"{funnel['total_conversions']:,}")
        with col3:
            st.metric("Conversion Rate", format_percentage(funnel['conversion_rate']))
        
        st.divider()
        
        # Detailed funnel visualization
        st.subheader("📊 Funnel Progression")
        
        funnel_df = pd.DataFrame(funnel['funnel_stages'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=funnel_df['stage'],
            y=funnel_df['users'],
            mode='lines+markers',
            name='Users',
            line=dict(color='#3B82F6', width=3),
            marker=dict(size=10, color='#0F172A'),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))
        
        fig.update_layout(
            height=400,
            title='User Progression Through Funnel',
            xaxis_title='Funnel Stage',
            yaxis_title='Unique Users',
            paper_bgcolor='white',
            plot_bgcolor='#F9FAFB',
            hovermode='x unified',
            font=dict(size=11)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Drop-off analysis table
        st.subheader("⚠️ Drop-off Analysis")
        
        dropoff_data = []
        for i, stage in enumerate(funnel['funnel_stages']):
            if i == 0:
                dropoff_pct = 0
            else:
                prev_users = funnel['funnel_stages'][i-1]['users']
                curr_users = stage['users']
                dropoff_pct = ((prev_users - curr_users) / prev_users) * 100
            
            dropoff_data.append({
                'Stage': stage['stage'].replace('_', ' ').title(),
                'Users': f"{stage['users']:,}",
                'Conversion %': f"{stage['percentage']:.2f}%",
                'Drop-off %': f"{dropoff_pct:.2f}%" if i > 0 else "N/A"
            })
        
        dropoff_df = pd.DataFrame(dropoff_data)
        st.dataframe(dropoff_df, use_container_width=True, hide_index=True)
        
        # Critical bottlenecks
        st.subheader("🎯 Critical Bottlenecks")
        
        col1, col2, col3 = st.columns(3)
        
        dropoffs_with_stage = []
        for i in range(1, len(funnel['funnel_stages'])):
            prev = funnel['funnel_stages'][i-1]
            curr = funnel['funnel_stages'][i]
            dropoff = ((prev['users'] - curr['users']) / prev['users']) * 100
            dropoffs_with_stage.append((curr['stage'], dropoff))
        
        top_3 = sorted(dropoffs_with_stage, key=lambda x: x[1], reverse=True)[:3]
        
        for idx, (stage, dropoff) in enumerate(top_3, 1):
            with [col1, col2, col3][idx-1]:
                st.html(f"""
                <div style='background: #FEF3C7; padding: 15px; border-radius: 8px; border-left: 4px solid #F59E0B;'>
                    <p style='margin: 0; color: #92400E; font-size: 12px; font-weight: 600;'>Bottleneck #{idx}</p>
                    <h4 style='margin: 8px 0 0 0; color: #78350F;'>{stage.replace('_', ' ').title()}</h4>
                    <p style='margin: 8px 0 0 0; color: #92400E; font-size: 16px; font-weight: 700;'>{dropoff:.1f}% Drop-off</p>
                </div>
                """)
    
    # ========================================================================
    # PAGE 3: COHORT & RETENTION
    # ========================================================================
    
    elif page == "👥 Cohort & Retention":
        st.header("👥 Cohort Analysis & Retention")
        
        cohort_retention, cohort_stats = analyzer_filtered.get_cohort_analysis()
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.html(create_metric_card(
                "30-Day Re-engagement Rate",
                format_percentage(cohort_stats['re_engagement_rate_30d']),
                "post-purchase",
                "success"
            ))
        
        with col2:
            st.html(create_metric_card(
                "Avg Revenue per Cohort",
                format_currency(cohort_stats['avg_revenue_per_cohort']),
                "monthly cohort average",
                "info"
            ))
        
        with col3:
            st.html(create_metric_card(
                "Total Revenue",
                format_currency(cohort_stats['total_revenue']),
                "across all cohorts",
                "success"
            ))
        
        st.divider()
        
        # Cohort retention heatmap
        st.subheader("📈 Cohort Retention Heatmap")
        
        fig = go.Figure(data=go.Heatmap(
            z=cohort_retention.values,
            x=cohort_retention.columns,
            y=cohort_retention.index.astype(str),
            colorscale='Greens',
            text=cohort_retention.values,
            texttemplate='%{text:.0f}%',
            textfont={"size": 10},
            colorbar=dict(title="Retention %")
        ))
        
        fig.update_layout(
            title='Customer Retention by Cohort (% of cohort size)',
            xaxis_title='Days Since First Purchase',
            yaxis_title='Cohort Month',
            height=400,
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Re-engagement opportunities
        st.subheader("🎯 Re-engagement Opportunities (First 30 Days)")
        
        early_purchases = df_filtered[df_filtered['days_in_cohort'] <= 30]
        reengagement_data = early_purchases.groupby(
            early_purchases['event_date'].dt.to_period('M')
        ).agg({
            'user_id': 'nunique',
            'converted': lambda x: (x.sum() / len(x)) * 100,
            'revenue': 'sum'
        }).reset_index()
        reengagement_data.columns = ['Cohort', 'Users', 'Re-engagement %', 'Revenue']
        reengagement_data['Cohort'] = reengagement_data['Cohort'].astype(str)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=reengagement_data['Cohort'],
            y=reengagement_data['Re-engagement %'],
            name='Re-engagement Rate',
            yaxis='y',
            marker_color='#10B981'
        ))
        
        fig.add_trace(go.Scatter(
            x=reengagement_data['Cohort'],
            y=reengagement_data['Revenue'],
            name='Revenue',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='#3B82F6', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            height=350,
            yaxis=dict(title='Re-engagement Rate (%)', side='left'),
            yaxis2=dict(title='Revenue ($)', overlaying='y', side='right'),
            paper_bgcolor='white',
            plot_bgcolor='#F9FAFB',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========================================================================
    # PAGE 4: REVENUE ANALYTICS
    # ========================================================================
    
    elif page == "💰 Revenue Analytics":
        st.header("💰 Revenue Analytics & Optimization")
        
        # Category performance
        st.subheader("📊 Revenue by Product Category")
        
        category_data = df_filtered.groupby('product_category').agg({
            'revenue': 'sum',
            'converted': 'sum',
            'user_id': 'nunique',
            'session_duration_sec': 'mean'
        }).sort_values('revenue', ascending=False).reset_index()
        
        category_data['conversion_rate'] = (
            (category_data['converted'] / category_data['user_id']) * 100
        ).round(2)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=category_data['product_category'],
            y=category_data['revenue'],
            name='Revenue',
            yaxis='y',
            marker_color='#3B82F6'
        ))
        
        fig.add_trace(go.Scatter(
            x=category_data['product_category'],
            y=category_data['conversion_rate'],
            name='Conversion Rate (%)',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='#10B981', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            height=350,
            yaxis=dict(title='Revenue ($)', side='left'),
            yaxis2=dict(title='Conversion Rate (%)', overlaying='y', side='right'),
            paper_bgcolor='white',
            plot_bgcolor='#F9FAFB',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Category table
        st.dataframe(
            category_data[[
                'product_category', 'revenue', 'converted', 'user_id', 'conversion_rate'
            ]].rename(columns={
                'product_category': 'Category',
                'revenue': 'Revenue',
                'converted': 'Conversions',
                'user_id': 'Users',
                'conversion_rate': 'Conv. Rate %'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        st.divider()
        
        # Average order value by segment
        st.subheader("💵 Average Order Value Analysis")
        
        aov_data = df_filtered[df_filtered['converted'] == 1].groupby(
            'customer_segment'
        )['revenue'].agg(['mean', 'median', 'count']).reset_index()
        aov_data.columns = ['Segment', 'Avg Value', 'Median Value', 'Orders']
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure(data=[go.Bar(
                x=aov_data['Segment'],
                y=aov_data['Avg Value'],
                marker_color=['#10B981', '#3B82F6'],
                text=aov_data['Avg Value'].round(2),
                textposition='auto'
            )])
            
            fig.update_layout(
                title='Average Order Value by Segment',
                height=300,
                paper_bgcolor='white',
                plot_bgcolor='#F9FAFB',
                xaxis_title='Customer Segment',
                yaxis_title='AOV ($)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(
                aov_data.rename(columns={
                    'Segment': 'Customer Segment',
                    'Avg Value': 'Avg AOV',
                    'Median Value': 'Median AOV',
                    'Orders': 'Total Orders'
                }),
                use_container_width=True,
                hide_index=True
            )
    
    # ========================================================================
    # PAGE 5: DEVICE & SOURCE ANALYSIS
    # ========================================================================
    
    elif page == "📱 Device & Source":
        st.header("📱 Device & Traffic Source Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📱 Device Performance")
            
            device_data = df_filtered.groupby('device').agg({
                'user_id': 'nunique',
                'converted': ['sum', lambda x: (x.sum()/len(x))*100],
                'revenue': 'sum',
                'session_duration_sec': 'mean'
            }).round(2)
            
            device_data.columns = ['Users', 'Conversions', 'Conv. Rate %', 'Revenue', 'Avg Session']
            device_data = device_data.reset_index()
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=device_data['device'],
                y=device_data['Conv. Rate %'],
                name='Conversion Rate',
                marker_color='#10B981'
            ))
            
            fig.update_layout(
                height=300,
                paper_bgcolor='white',
                plot_bgcolor='#F9FAFB',
                xaxis_title='Device Type',
                yaxis_title='Conversion Rate (%)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(device_data, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("🔗 Traffic Source Performance")
            
            source_data = df_filtered.groupby('traffic_source').agg({
                'user_id': 'nunique',
                'converted': ['sum', lambda x: (x.sum()/len(x))*100],
                'revenue': 'sum'
            }).sort_values(('revenue', 'sum'), ascending=False).round(2)
            
            source_data.columns = ['Users', 'Conversions', 'Conv. Rate %', 'Revenue']
            source_data = source_data.reset_index()
            
            fig = px.pie(
                source_data,
                values='Revenue',
                names='traffic_source',
                title='Revenue Distribution by Source',
                hole=0.3,
                color_discrete_sequence=['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']
            )
            
            fig.update_layout(height=350, paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(source_data, use_container_width=True, hide_index=True)
    
    # ========================================================================
    # PAGE 6: DETAILED REPORTS
    # ========================================================================
    
    elif page == "🔍 Detailed Reports":
        st.header("🔍 Detailed Analysis Reports")
        
        report_type = st.selectbox(
            "Select Report Type",
            ["Geographic Performance", "Customer Lifecycle", "Product Performance", "Session Analysis"]
        )
        
        if report_type == "Geographic Performance":
            st.subheader("🌍 Geographic Performance")
            
            geo_data = df_filtered.groupby('country').agg({
                'user_id': 'nunique',
                'converted': ['sum', lambda x: (x.sum()/len(x))*100],
                'revenue': 'sum'
            }).sort_values(('revenue', 'sum'), ascending=False).round(2)
            
            geo_data.columns = ['Users', 'Conversions', 'Conv. Rate %', 'Revenue']
            geo_data = geo_data.reset_index().rename(columns={'country': 'Country'})
            
            fig = go.Figure(data=[
                go.Bar(x=geo_data['Country'], y=geo_data['Revenue'], marker_color='#3B82F6')
            ])
            
            fig.update_layout(
                title='Revenue by Country',
                height=400,
                paper_bgcolor='white',
                plot_bgcolor='#F9FAFB',
                xaxis_title='Country',
                yaxis_title='Revenue ($)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(geo_data, use_container_width=True, hide_index=True)
        
        elif report_type == "Customer Lifecycle":
            st.subheader("👥 Customer Lifecycle Analysis")
            
            lifecycle = df_filtered.groupby('customer_segment').agg({
                'user_id': 'nunique',
                'repeat_purchases': 'mean',
                'converted': lambda x: (x.sum()/len(x))*100,
                'revenue': ['sum', 'mean']
            }).round(2)
            
            col1, col2 = st.columns(2)
            
            new_customers = df_filtered[df_filtered['customer_segment'] == 'New']
            repeat_customers = df_filtered[df_filtered['customer_segment'] == 'Repeat']
            
            with col1:
                st.metric(
                    "New Customer Conversion",
                    format_percentage((new_customers['converted'].sum() / len(new_customers)) * 100)
                )
            with col2:
                st.metric(
                    "Repeat Customer Conversion",
                    format_percentage((repeat_customers['converted'].sum() / len(repeat_customers)) * 100)
                )
            
            segment_comp = df_filtered.groupby('customer_segment').agg({
                'user_id': 'nunique',
                'revenue': 'sum',
                'session_duration_sec': 'mean'
            }).reset_index()
            
            st.dataframe(segment_comp, use_container_width=True, hide_index=True)
        
        elif report_type == "Product Performance":
            st.subheader("📦 Top Products Analysis")
            
            top_products = df_filtered.groupby('product_id').agg({
                'user_id': 'nunique',
                'converted': 'sum',
                'product_price': 'mean',
                'revenue': 'sum'
            }).sort_values('revenue', ascending=False).head(10).reset_index()
            
            top_products.columns = ['Product ID', 'Users', 'Conversions', 'Avg Price', 'Total Revenue']
            
            st.dataframe(top_products, use_container_width=True, hide_index=True)
        
        else:  # Session Analysis
            st.subheader("⏱️ Session Analysis")
            
            session_stats = df_filtered.groupby('funnel_stage')['session_duration_sec'].agg([
                'mean', 'median', 'min', 'max', 'std'
            ]).round(2).reset_index()
            
            session_stats.columns = ['Funnel Stage', 'Avg Duration', 'Median', 'Min', 'Max', 'Std Dev']
            
            st.dataframe(session_stats, use_container_width=True, hide_index=True)
    
    # Footer
    st.divider()
    st.caption(
        "📊 E-commerce Analytics Hub | Data: 100K+ transactions | Last Updated: " +
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


if __name__ == "__main__":
    main()