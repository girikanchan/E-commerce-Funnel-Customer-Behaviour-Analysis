"""
E-commerce Data Generator
Generates 100K+ realistic transaction records with customer journey funnel stages
Part of MVT Architecture - Model Layer
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import Tuple


class EcommerceDataGenerator:
    """Generate synthetic e-commerce data for funnel and cohort analysis"""
    
    FUNNEL_STAGES = [
        'landing_page_view',
        'product_browse',
        'product_view',
        'add_to_cart',
        'checkout_start',
        'payment_info',
        'order_placed'
    ]
    
    # Drop-off rates - continuation percentage at each stage
    CONTINUATION_RATES = {
        'landing_page_view': 1.0,
        'product_browse': 0.85,
        'product_view': 0.72,
        'add_to_cart': 0.58,
        'checkout_start': 0.45,
        'payment_info': 0.35,
        'order_placed': 0.31
    }
    
    CATEGORIES = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Beauty', 'Toys']
    DEVICES = ['Mobile', 'Desktop', 'Tablet']
    SOURCES = ['Organic', 'Paid Search', 'Social Media', 'Email', 'Referral', 'Direct']
    COUNTRIES = ['US', 'UK', 'CA', 'AU', 'DE', 'FR', 'JP', 'IN']
    
    def __init__(self, seed: int = 42):
        """Initialize generator with random seed"""
        np.random.seed(seed)
        random.seed(seed)
    
    def generate(self, n_records: int = 100000) -> pd.DataFrame:
        """
        Generate synthetic e-commerce transaction data
        
        Args:
            n_records: Number of transaction records to generate
            
        Returns:
            DataFrame with transaction records
        """
        records = []
        
        for i in range(n_records):
            record = self._create_record(i)
            records.append(record)
        
        df = pd.DataFrame(records)
        df = self._enrich_dataframe(df)
        
        return df
    
    def _create_record(self, index: int) -> dict:
        """Create a single transaction record"""
        user_id = f"USER_{index:06d}"
        session_id = f"SESSION_{index:08d}"
        
        # Randomize dates over 12 months
        days_ago = random.randint(1, 365)
        event_time = datetime.now() - timedelta(days=days_ago)
        
        # Determine which funnel stage user reaches
        reached_stage = self._determine_funnel_stage()
        
        # Product details
        product_category = random.choice(self.CATEGORIES)
        product_id = f"PROD_{random.randint(1000, 9999)}"
        product_price = round(np.random.lognormal(3.5, 1.2), 2)
        
        # Customer attributes
        device = random.choice(self.DEVICES)
        source = random.choice(self.SOURCES)
        country = random.choice(self.COUNTRIES)
        
        # Session duration increases with funnel progression
        stage_index = self.FUNNEL_STAGES.index(reached_stage)
        session_duration = max(10, int(30 + (stage_index * 120) + np.random.normal(0, 50)))
        
        # Conversion metrics
        converted = 1 if reached_stage == 'order_placed' else 0
        revenue = product_price if converted else 0
        quantity = random.randint(1, 5) if converted else 0
        
        # Customer profile
        is_new_customer = random.choice([True, False])
        repeat_purchases = random.randint(0, 15) if not is_new_customer else 0
        
        return {
            'user_id': user_id,
            'session_id': session_id,
            'event_time': event_time,
            'event_date': event_time.date(),
            'funnel_stage': reached_stage,
            'product_category': product_category,
            'product_id': product_id,
            'product_price': product_price,
            'device': device,
            'traffic_source': source,
            'country': country,
            'session_duration_sec': session_duration,
            'converted': converted,
            'revenue': revenue,
            'quantity': quantity,
            'is_new_customer': is_new_customer,
            'repeat_purchases': repeat_purchases,
            'days_since_last_purchase': random.randint(1, 365) if not is_new_customer else None
        }
    
    def _determine_funnel_stage(self) -> str:
        """Determine which funnel stage user reaches based on drop-off rates"""
        rand_val = random.random()
        cumulative = 0
        
        for stage in self.FUNNEL_STAGES:
            cumulative += (1 - self.CONTINUATION_RATES[stage])
            if rand_val < cumulative:
                return stage
        
        return 'order_placed'
    
    def _enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived columns to dataframe"""
        df['event_date'] = pd.to_datetime(df['event_date'])
        df['event_time'] = pd.to_datetime(df['event_time'])
        
        # Cohort analysis columns
        df['cohort_month'] = df['event_date'].dt.to_period('M')
        df['days_in_cohort'] = (pd.Timestamp.now() - df['event_date']).dt.days
        
        # Customer segment
        df['customer_segment'] = df.apply(
            lambda x: 'New' if x['is_new_customer'] else 'Repeat', axis=1
        )
        
        # Device group
        df['device_group'] = df['device'].apply(
            lambda x: 'Mobile' if x == 'Mobile' else 'Desktop & Tablet'
        )
        
        return df


class DataAnalyzer:
    """Analyze e-commerce data for funnel and cohort insights"""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize analyzer with data"""
        self.df = df
    
    def get_funnel_analysis(self) -> dict:
        """Analyze funnel stages and drop-off rates"""
        funnel_stages = [
            'landing_page_view', 'product_browse', 'product_view',
            'add_to_cart', 'checkout_start', 'payment_info', 'order_placed'
        ]
        
        funnel_data = []
        total_users = len(self.df['user_id'].unique())
        
        for stage in funnel_stages:
            users_at_stage = len(self.df[self.df['funnel_stage'] == stage]['user_id'].unique())
            percentage = (users_at_stage / total_users) * 100
            drop_off = 100 - percentage if funnel_data else 0
            
            funnel_data.append({
                'stage': stage,
                'users': users_at_stage,
                'percentage': round(percentage, 2),
                'drop_off': round(drop_off, 2) if funnel_data else 0
            })
        
        return {
            'funnel_stages': funnel_data,
            'total_users': total_users,
            'total_conversions': len(self.df[self.df['converted'] == 1]),
            'conversion_rate': round((len(self.df[self.df['converted'] == 1]) / total_users) * 100, 2)
        }
    
    def get_cohort_analysis(self) -> Tuple[pd.DataFrame, dict]:
        """Analyze customer cohorts and retention"""
        # Create cohort analysis table
        cohort_data = self.df.groupby(['cohort_month', 'days_in_cohort']).agg({
            'user_id': 'nunique',
            'converted': 'sum',
            'revenue': 'sum'
        }).reset_index()
        
        cohort_retention = cohort_data.pivot_table(
            index='cohort_month',
            columns='days_in_cohort',
            values='user_id',
            aggfunc='sum'
        )
        
        # Normalize by cohort size
        cohort_retention = cohort_retention.divide(cohort_retention.iloc[:, 0], axis=0) * 100
        
        # Get 30-day re-engagement stats
        early_days = self.df[self.df['days_in_cohort'] <= 30]
        re_engagement_rate = (early_days[early_days['converted'] == 1].shape[0] / 
                             len(early_days['user_id'].unique())) * 100
        
        return cohort_retention, {
            're_engagement_rate_30d': round(re_engagement_rate, 2),
            'avg_revenue_per_cohort': round(self.df.groupby('cohort_month')['revenue'].mean().mean(), 2),
            'total_revenue': round(self.df['revenue'].sum(), 2)
        }
    
    def get_kpi_metrics(self) -> dict:
        """Calculate key KPI metrics"""
        total_revenue = self.df['revenue'].sum()
        total_transactions = len(self.df)
        unique_users = len(self.df['user_id'].unique())
        conversions = len(self.df[self.df['converted'] == 1])
        
        return {
            'total_revenue': round(total_revenue, 2),
            'conversion_rate': round((conversions / unique_users) * 100, 2),
            'avg_order_value': round(total_revenue / conversions if conversions > 0 else 0, 2),
            'revenue_per_user': round(total_revenue / unique_users, 2),
            'total_users': unique_users,
            'total_conversions': conversions,
            'avg_session_duration': round(self.df['session_duration_sec'].mean(), 2)
        }
    
    def get_segment_analysis(self) -> dict:
        """Analyze performance by customer segments"""
        segments = self.df.groupby('customer_segment').agg({
            'user_id': 'nunique',
            'converted': ['sum', 'mean'],
            'revenue': 'sum',
            'session_duration_sec': 'mean'
        }).round(2)
        
        return segments.to_dict()
    
    def get_device_analysis(self) -> dict:
        """Analyze performance by device type"""
        device_analysis = self.df.groupby('device').agg({
            'user_id': 'nunique',
            'converted': ['sum', lambda x: (x.sum() / len(x)) * 100],
            'revenue': 'sum',
            'session_duration_sec': 'mean'
        }).round(2)
        
        return device_analysis.to_dict()
    
    def get_source_analysis(self) -> dict:
        """Analyze performance by traffic source"""
        source_analysis = self.df.groupby('traffic_source').agg({
            'user_id': 'nunique',
            'converted': 'sum',
            'revenue': 'sum'
        }).sort_values('revenue', ascending=False).round(2)
        
        return source_analysis.to_dict()