"""
SQL Queries and PySpark Processing Layer
Part of MVT Architecture - Model Layer
Handles database operations and distributed data processing
"""

from typing import List, Dict, Tuple
import pandas as pd


class SQLQueries:
    """SQL queries for e-commerce analysis"""
    
    # Funnel Analysis Query
    FUNNEL_ANALYSIS = """
    SELECT 
        funnel_stage,
        COUNT(DISTINCT user_id) as users_count,
        COUNT(*) as total_events,
        ROUND(100.0 * COUNT(DISTINCT user_id) / 
            (SELECT COUNT(DISTINCT user_id) FROM transactions) , 2) as percentage,
        ROUND(AVG(session_duration_sec), 2) as avg_session_duration
    FROM transactions
    GROUP BY funnel_stage
    ORDER BY 
        CASE 
            WHEN funnel_stage = 'landing_page_view' THEN 1
            WHEN funnel_stage = 'product_browse' THEN 2
            WHEN funnel_stage = 'product_view' THEN 3
            WHEN funnel_stage = 'add_to_cart' THEN 4
            WHEN funnel_stage = 'checkout_start' THEN 5
            WHEN funnel_stage = 'payment_info' THEN 6
            WHEN funnel_stage = 'order_placed' THEN 7
        END
    """
    
    # Conversion Rate by Device
    CONVERSION_BY_DEVICE = """
    SELECT 
        device,
        COUNT(DISTINCT user_id) as users,
        SUM(converted) as conversions,
        ROUND(100.0 * SUM(converted) / COUNT(DISTINCT user_id), 2) as conversion_rate,
        ROUND(AVG(revenue), 2) as avg_revenue
    FROM transactions
    GROUP BY device
    ORDER BY conversion_rate DESC
    """
    
    # Conversion by Traffic Source
    CONVERSION_BY_SOURCE = """
    SELECT 
        traffic_source,
        COUNT(DISTINCT user_id) as users,
        SUM(converted) as conversions,
        ROUND(100.0 * SUM(converted) / COUNT(DISTINCT user_id), 2) as conversion_rate,
        ROUND(SUM(revenue), 2) as total_revenue,
        ROUND(AVG(revenue), 2) as avg_revenue_per_user
    FROM transactions
    GROUP BY traffic_source
    ORDER BY total_revenue DESC
    """
    
    # Cohort Retention Query - 30 Day Analysis
    COHORT_30_DAY_RETENTION = """
    WITH cohort_data AS (
        SELECT 
            DATE_TRUNC('month', event_date) as cohort_month,
            user_id,
            event_date,
            converted,
            revenue
        FROM transactions
    ),
    cohort_size AS (
        SELECT 
            cohort_month,
            COUNT(DISTINCT user_id) as cohort_users
        FROM cohort_data
        GROUP BY cohort_month
    )
    SELECT 
        cd.cohort_month,
        COUNT(DISTINCT cd.user_id) as total_users,
        SUM(CASE WHEN cd.converted = 1 THEN 1 ELSE 0 END) as conversions,
        ROUND(100.0 * SUM(cd.converted) / COUNT(DISTINCT cd.user_id), 2) as conversion_rate,
        ROUND(AVG(cd.revenue), 2) as avg_revenue_per_user,
        ROUND(SUM(cd.revenue), 2) as total_revenue
    FROM cohort_data cd
    WHERE EXTRACT(DAY FROM (CURRENT_DATE - cd.event_date)) <= 30
    GROUP BY cd.cohort_month
    ORDER BY cd.cohort_month DESC
    """
    
    # Re-engagement Opportunities - First 30 Days
    REENGAGEMENT_OPPORTUNITIES = """
    SELECT 
        cohort_month,
        COUNT(DISTINCT user_id) as users_in_30d,
        SUM(converted) as purchases_in_30d,
        ROUND(100.0 * SUM(converted) / COUNT(DISTINCT user_id), 2) as reengagement_rate,
        ROUND(AVG(revenue), 2) as avg_purchase_value,
        COUNT(DISTINCT product_category) as categories_browsed
    FROM transactions
    WHERE EXTRACT(DAY FROM (CURRENT_DATE - event_date)) <= 30
    GROUP BY cohort_month
    ORDER BY reengagement_rate DESC
    """
    
    # Category Performance Analysis
    CATEGORY_PERFORMANCE = """
    SELECT 
        product_category,
        COUNT(DISTINCT user_id) as users,
        SUM(converted) as conversions,
        ROUND(100.0 * SUM(converted) / COUNT(DISTINCT user_id), 2) as conversion_rate,
        ROUND(AVG(product_price), 2) as avg_price,
        ROUND(SUM(revenue), 2) as total_revenue,
        ROUND(AVG(session_duration_sec), 2) as avg_session_duration
    FROM transactions
    GROUP BY product_category
    ORDER BY total_revenue DESC
    """
    
    # Customer Lifecycle Analysis
    CUSTOMER_LIFECYCLE = """
    SELECT 
        customer_segment,
        COUNT(DISTINCT user_id) as total_customers,
        AVG(repeat_purchases) as avg_repeat_purchases,
        ROUND(100.0 * SUM(converted) / COUNT(*), 2) as conversion_rate,
        ROUND(AVG(revenue), 2) as avg_revenue,
        ROUND(SUM(revenue), 2) as total_revenue
    FROM transactions
    GROUP BY customer_segment
    ORDER BY total_revenue DESC
    """
    
    # Top Drop-off Points
    TOP_DROPOFF_POINTS = """
    WITH funnel_progression AS (
        SELECT 
            funnel_stage,
            COUNT(DISTINCT user_id) as users,
            LAG(COUNT(DISTINCT user_id)) OVER (
                ORDER BY CASE 
                    WHEN funnel_stage = 'landing_page_view' THEN 1
                    WHEN funnel_stage = 'product_browse' THEN 2
                    WHEN funnel_stage = 'product_view' THEN 3
                    WHEN funnel_stage = 'add_to_cart' THEN 4
                    WHEN funnel_stage = 'checkout_start' THEN 5
                    WHEN funnel_stage = 'payment_info' THEN 6
                    WHEN funnel_stage = 'order_placed' THEN 7
                END
            ) as previous_stage_users
        FROM transactions
        GROUP BY funnel_stage
    )
    SELECT 
        funnel_stage,
        users,
        previous_stage_users,
        ROUND(100.0 * (previous_stage_users - users) / previous_stage_users, 2) as dropoff_rate
    FROM funnel_progression
    WHERE previous_stage_users IS NOT NULL
    ORDER BY dropoff_rate DESC
    """
    
    # Geographic Performance
    GEOGRAPHIC_PERFORMANCE = """
    SELECT 
        country,
        COUNT(DISTINCT user_id) as users,
        SUM(converted) as conversions,
        ROUND(100.0 * SUM(converted) / COUNT(DISTINCT user_id), 2) as conversion_rate,
        ROUND(SUM(revenue), 2) as total_revenue,
        ROUND(AVG(revenue), 2) as avg_revenue
    FROM transactions
    GROUP BY country
    ORDER BY total_revenue DESC
    """


class PySparkProcessor:
    """
    PySpark data processing for large-scale e-commerce analytics
    Handles distributed processing of 100K+ records
    """
    
    @staticmethod
    def calculate_funnel_metrics(spark_df) -> Dict:
        """
        Calculate comprehensive funnel metrics using PySpark
        """
        from pyspark.sql import functions as F
        
        funnel_stages = [
            'landing_page_view', 'product_browse', 'product_view',
            'add_to_cart', 'checkout_start', 'payment_info', 'order_placed'
        ]
        
        total_users = spark_df.select('user_id').distinct().count()
        
        funnel_metrics = []
        for stage in funnel_stages:
            users_at_stage = spark_df.filter(
                spark_df.funnel_stage == stage
            ).select('user_id').distinct().count()
            
            percentage = (users_at_stage / total_users) * 100
            
            funnel_metrics.append({
                'stage': stage,
                'users': users_at_stage,
                'percentage': round(percentage, 2)
            })
        
        return {
            'funnel_metrics': funnel_metrics,
            'total_users': total_users,
            'conversion_rate': round(
                (spark_df.filter(spark_df.converted == 1).count() / total_users) * 100, 2
            )
        }
    
    @staticmethod
    def calculate_cohort_retention(spark_df) -> pd.DataFrame:
        """
        Calculate cohort-based retention using PySpark
        """
        from pyspark.sql import functions as F, Window
        
        # Create cohort analysis
        cohort_data = spark_df.groupBy(
            F.date_trunc('month', 'event_date').alias('cohort_month')
        ).agg(
            F.count(F.when(F.col('converted') == 1, 1)).alias('conversions'),
            F.countDistinct('user_id').alias('users'),
            F.avg('revenue').alias('avg_revenue')
        ).orderBy('cohort_month', ascending=False)
        
        return cohort_data.toPandas()
    
    @staticmethod
    def calculate_reengagement_opportunities(spark_df) -> pd.DataFrame:
        """
        Identify high-impact re-engagement opportunities in first 30 days
        """
        from pyspark.sql import functions as F
        
        thirty_days_ago = F.current_date() - F.expr('INTERVAL 30 DAY')
        
        reengagement = spark_df.filter(
            spark_df.event_date >= thirty_days_ago
        ).groupBy(
            F.date_trunc('month', 'event_date').alias('cohort_month')
        ).agg(
            F.countDistinct('user_id').alias('users'),
            F.sum(F.when(F.col('converted') == 1, 1)).alias('conversions'),
            F.avg('revenue').alias('avg_revenue')
        ).orderBy('conversions', ascending=False)
        
        return reengagement.toPandas()
    
    @staticmethod
    def calculate_segment_performance(spark_df) -> pd.DataFrame:
        """
        Calculate performance metrics by customer segment
        """
        from pyspark.sql import functions as F
        
        segment_performance = spark_df.groupBy('customer_segment').agg(
            F.countDistinct('user_id').alias('users'),
            F.sum(F.when(F.col('converted') == 1, 1)).alias('conversions'),
            (F.sum(F.when(F.col('converted') == 1, 1)) / 
             F.countDistinct('user_id')).alias('conversion_rate'),
            F.sum('revenue').alias('total_revenue'),
            F.avg('revenue').alias('avg_revenue')
        )
        
        return segment_performance.toPandas()


class QueryBuilder:
    """Dynamic SQL query builder for flexible analysis"""
    
    def __init__(self):
        self.base_query = "SELECT * FROM transactions WHERE 1=1"
        self.conditions = []
    
    def add_date_filter(self, start_date: str, end_date: str) -> 'QueryBuilder':
        """Add date range filter"""
        self.conditions.append(
            f"event_date BETWEEN '{start_date}' AND '{end_date}'"
        )
        return self
    
    def add_device_filter(self, devices: List[str]) -> 'QueryBuilder':
        """Add device type filter"""
        devices_str = "', '".join(devices)
        self.conditions.append(f"device IN ('{devices_str}')")
        return self
    
    def add_source_filter(self, sources: List[str]) -> 'QueryBuilder':
        """Add traffic source filter"""
        sources_str = "', '".join(sources)
        self.conditions.append(f"traffic_source IN ('{sources_str}')")
        return self
    
    def add_country_filter(self, countries: List[str]) -> 'QueryBuilder':
        """Add country filter"""
        countries_str = "', '".join(countries)
        self.conditions.append(f"country IN ('{countries_str}')")
        return self
    
    def add_conversion_filter(self, converted: bool = True) -> 'QueryBuilder':
        """Add conversion filter"""
        self.conditions.append(f"converted = {1 if converted else 0}")
        return self
    
    def build(self) -> str:
        """Build final query"""
        for condition in self.conditions:
            self.base_query += f" AND {condition}"
        return self.base_query
    
    def reset(self) -> 'QueryBuilder':
        """Reset query builder"""
        self.base_query = "SELECT * FROM transactions WHERE 1=1"
        self.conditions = []
        return self