"""
📊 E-COMMERCE ANALYTICS DASHBOARD
==================================
Interactive dashboard for visualizing Etsy shop analytics with comprehensive insights
Includes authentication for secure access to sensitive business data
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from prisma import Prisma
from prisma.enums import PeriodType
import hashlib
import os
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

# Load environment variables
load_dotenv()

# Authentication configuration
def get_credentials():
    """Get credentials from environment variables or use defaults"""
    # Read from .env file or environment
    username = os.getenv('DASHBOARD_USERNAME', 'admin')
    password = os.getenv('DASHBOARD_PASSWORD', 'changeme123')
    
    # Hash the password for comparison
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    return {username: password_hash}

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated

def login_page():
    """Display login page"""
    st.markdown('<h1 class="main-header">🔐 Etsy Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔒 Please Login to Continue")
        st.markdown("Access to this dashboard requires authentication due to sensitive business data.")
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submit:
                if username and password:
                    credentials = get_credentials()
                    password_hash = hash_password(password)
                    
                    if username in credentials and credentials[username] == password_hash:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.success("✅ Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter both username and password")
        
        # Security notice
        st.markdown("---")
        st.info("""
        **🔐 Security Notice:**
        - Set custom credentials in your `.env` file
        - Add: `DASHBOARD_USERNAME=your_username`
        - Add: `DASHBOARD_PASSWORD=your_secure_password`
        - Default credentials should be changed immediately
        """)

def logout():
    """Logout the user"""
    st.session_state.authenticated = False
    if 'username' in st.session_state:
        del st.session_state.username
    st.rerun()

# Page configuration
st.set_page_config(
    page_title="Etsy Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)


class DashboardDataLoader:
    """Handle all database operations asynchronously"""
    
    def __init__(self):
        self.prisma = Prisma()
    
    async def connect(self):
        """Connect to database"""
        if not self.prisma.is_connected():
            await self.prisma.connect()
    
    async def disconnect(self):
        """Disconnect from database"""
        if self.prisma.is_connected():
            await self.prisma.disconnect()
    
    async def get_shop_reports(self, period_type: str, start_date: datetime, end_date: datetime):
        """Fetch shop reports from database"""
        period_enum = {
            "Yearly": PeriodType.YEARLY,
            "Monthly": PeriodType.MONTHLY,
            "Weekly": PeriodType.WEEKLY
        }[period_type]
        
        reports = await self.prisma.shopreport.find_many(
            where={
                "periodType": period_enum,
                "periodStart": {"gte": start_date},
                "periodEnd": {"lte": end_date}
            },
            order={"periodStart": "asc"}
        )
        return reports
    
    async def get_listing_reports(self, period_type: str, start_date: datetime, end_date: datetime, 
                                  listing_id: int = None):
        """Fetch listing reports from database"""
        period_enum = {
            "Yearly": PeriodType.YEARLY,
            "Monthly": PeriodType.MONTHLY,
            "Weekly": PeriodType.WEEKLY
        }[period_type]
        
        where_clause = {
            "periodType": period_enum,
            "periodStart": {"gte": start_date},
            "periodEnd": {"lte": end_date}
        }
        
        if listing_id:
            # Ensure listingId is an integer (BigInt in DB)
            where_clause["listingId"] = int(listing_id)
        
        reports = await self.prisma.listingreport.find_many(
            where=where_clause,
            order={"periodStart": "asc"}
        )
        return reports
    
    async def get_product_reports(self, period_type: str, start_date: datetime, end_date: datetime,
                                 sku: str = None):
        """Fetch product reports from database"""
        period_enum = {
            "Yearly": PeriodType.YEARLY,
            "Monthly": PeriodType.MONTHLY,
            "Weekly": PeriodType.WEEKLY
        }[period_type]
        
        where_clause = {
            "periodType": period_enum,
            "periodStart": {"gte": start_date},
            "periodEnd": {"lte": end_date}
        }
        
        if sku:
            where_clause["sku"] = sku
        
        reports = await self.prisma.productreport.find_many(
            where=where_clause,
            order={"periodStart": "asc"}
        )
        return reports
    
    async def get_all_listings(self):
        """Get all listing IDs with their titles"""
        listings = await self.prisma.listing.find_many(
            order={"listingId": "asc"}
        )
        return listings
    
    async def get_all_skus(self):
        """Get all unique SKUs"""
        products = await self.prisma.listingproduct.find_many(
            where={
                "sku": {"not": None},
                "isDeleted": False
            },
            distinct=["sku"],
        )
        return [p.sku for p in products if p.sku]
    
    async def get_date_range(self):
        """Get available date range from orders"""
        try:
            earliest = await self.prisma.order.find_first(order={"createdTimestamp": "asc"})
            latest = await self.prisma.order.find_first(order={"createdTimestamp": "desc"})
            
            if earliest and latest:
                start_date = datetime.fromtimestamp(earliest.createdTimestamp)
                end_date = datetime.fromtimestamp(latest.createdTimestamp)
                return start_date, end_date
        except:
            pass
        
        # Fallback to reasonable defaults
        return datetime.now() - timedelta(days=365), datetime.now()


def convert_reports_to_dataframe(reports):
    """Convert Prisma report objects to pandas DataFrame"""
    if not reports:
        return pd.DataFrame()
    
    data = []
    for report in reports:
        # Convert Prisma model to dict
        report_dict = report.dict()
        data.append(report_dict)
    
    df = pd.DataFrame(data)
    
    # Convert datetime columns
    if 'periodStart' in df.columns:
        df['periodStart'] = pd.to_datetime(df['periodStart'])
    if 'periodEnd' in df.columns:
        df['periodEnd'] = pd.to_datetime(df['periodEnd'])
    
    # Convert listingId to string to prevent scientific notation in plots
    if 'listingId' in df.columns:
        df['listingId'] = df['listingId'].astype(str)
    
    return df


def aggregate_reports_by_period(df: pd.DataFrame):
    """Aggregate multiple listing/product reports by period for cleaner visualization"""
    if df.empty:
        return df
    
    # Check if we have multiple entities (listings or products) that need aggregation
    has_listings = 'listingId' in df.columns
    has_skus = 'sku' in df.columns
    
    if not has_listings and not has_skus:
        # Already aggregated (shop reports)
        return df
    
    # Build aggregation dictionary based on available columns
    agg_dict = {'periodEnd': 'first'}
    
    # Sum columns - only include if they exist
    sum_columns = [
        'grossRevenue', 'netRevenue', 'productRevenue', 'totalShippingCharged',
        'totalGiftWrapRevenue', 'totalTaxes', 'totalVAT', 'productCost',
        'totalShippingCost', 'totalTransactionCosts', 'totalEtsyFees', 
        'totalOtherFees', 'totalCosts', 'grossProfit', 'netProfit',
        'totalOrders', 'cancelledOrders', 'refundedOrders', 'totalRefunds',
        'totalItemsSold', 'uniqueCustomers', 'repeatCustomers', 
        'totalViews', 'totalVisits'
    ]
    
    for col in sum_columns:
        if col in df.columns:
            agg_dict[col] = 'sum'
    
    # Calculate weighted averages for rates/margins (only if columns exist)
    weighted_cols = []
    
    if 'grossMargin' in df.columns and 'grossRevenue' in df.columns:
        df['grossMargin_weighted'] = df['grossMargin'] * df['grossRevenue']
        agg_dict['grossMargin_weighted'] = 'sum'
        weighted_cols.append('grossMargin_weighted')
    
    if 'netMargin' in df.columns and 'grossRevenue' in df.columns:
        df['netMargin_weighted'] = df['netMargin'] * df['grossRevenue']
        agg_dict['netMargin_weighted'] = 'sum'
        weighted_cols.append('netMargin_weighted')
    
    if 'markupRatio' in df.columns and 'grossRevenue' in df.columns:
        df['markupRatio_weighted'] = df['markupRatio'] * df['grossRevenue']
        agg_dict['markupRatio_weighted'] = 'sum'
        weighted_cols.append('markupRatio_weighted')
    
    if 'etsyFeeRate' in df.columns and 'grossRevenue' in df.columns:
        df['etsyFeeRate_weighted'] = df['etsyFeeRate'] * df['grossRevenue']
        agg_dict['etsyFeeRate_weighted'] = 'sum'
        weighted_cols.append('etsyFeeRate_weighted')
    
    if 'takeHomeRate' in df.columns and 'grossRevenue' in df.columns:
        df['takeHomeRate_weighted'] = df['takeHomeRate'] * df['grossRevenue']
        agg_dict['takeHomeRate_weighted'] = 'sum'
        weighted_cols.append('takeHomeRate_weighted')
    
    if 'conversionRate' in df.columns and 'totalVisits' in df.columns:
        df['conversionRate_weighted'] = df['conversionRate'] * df['totalVisits']
        agg_dict['conversionRate_weighted'] = 'sum'
        weighted_cols.append('conversionRate_weighted')
    
    if 'customerRetentionRate' in df.columns and 'uniqueCustomers' in df.columns:
        df['customerRetentionRate_weighted'] = df['customerRetentionRate'] * df['uniqueCustomers']
        agg_dict['customerRetentionRate_weighted'] = 'sum'
        weighted_cols.append('customerRetentionRate_weighted')
    
    # Perform aggregation
    aggregated = df.groupby('periodStart').agg(agg_dict).reset_index()
    
    # Calculate weighted averages (only if we created weighted columns)
    if 'grossMargin_weighted' in aggregated.columns and 'grossRevenue' in aggregated.columns:
        aggregated['grossMargin'] = aggregated['grossMargin_weighted'] / aggregated['grossRevenue'].replace(0, 1)
    
    if 'netMargin_weighted' in aggregated.columns and 'grossRevenue' in aggregated.columns:
        aggregated['netMargin'] = aggregated['netMargin_weighted'] / aggregated['grossRevenue'].replace(0, 1)
    
    if 'markupRatio_weighted' in aggregated.columns and 'grossRevenue' in aggregated.columns:
        aggregated['markupRatio'] = aggregated['markupRatio_weighted'] / aggregated['grossRevenue'].replace(0, 1)
    
    if 'etsyFeeRate_weighted' in aggregated.columns and 'grossRevenue' in aggregated.columns:
        aggregated['etsyFeeRate'] = aggregated['etsyFeeRate_weighted'] / aggregated['grossRevenue'].replace(0, 1)
    
    if 'takeHomeRate_weighted' in aggregated.columns and 'grossRevenue' in aggregated.columns:
        aggregated['takeHomeRate'] = aggregated['takeHomeRate_weighted'] / aggregated['grossRevenue'].replace(0, 1)
    
    if 'conversionRate_weighted' in aggregated.columns and 'totalVisits' in aggregated.columns:
        aggregated['conversionRate'] = aggregated['conversionRate_weighted'] / aggregated['totalVisits'].replace(0, 1)
    
    if 'customerRetentionRate_weighted' in aggregated.columns and 'uniqueCustomers' in aggregated.columns:
        aggregated['customerRetentionRate'] = aggregated['customerRetentionRate_weighted'] / aggregated['uniqueCustomers'].replace(0, 1)
    
    # Calculate derived metrics (only if required columns exist)
    if 'grossRevenue' in aggregated.columns and 'totalOrders' in aggregated.columns:
        aggregated['averageOrderValue'] = aggregated['grossRevenue'] / aggregated['totalOrders'].replace(0, 1)
    
    if 'productRevenue' in aggregated.columns and 'totalItemsSold' in aggregated.columns:
        aggregated['averageItemPrice'] = aggregated['productRevenue'] / aggregated['totalItemsSold'].replace(0, 1)
    
    if 'totalShippingCharged' in aggregated.columns and 'grossRevenue' in aggregated.columns:
        aggregated['shippingRate'] = aggregated['totalShippingCharged'] / aggregated['grossRevenue'].replace(0, 1)
    
    if 'totalOrders' in aggregated.columns and 'cancelledOrders' in aggregated.columns:
        aggregated['completionRate'] = (aggregated['totalOrders'] - aggregated['cancelledOrders']) / aggregated['totalOrders'].replace(0, 1)
    
    if 'refundedOrders' in aggregated.columns and 'totalOrders' in aggregated.columns:
        aggregated['refundRate'] = aggregated['refundedOrders'] / aggregated['totalOrders'].replace(0, 1)
    
    if 'totalRefunds' in aggregated.columns and 'grossRevenue' in aggregated.columns:
        aggregated['refundRateByValue'] = aggregated['totalRefunds'] / aggregated['grossRevenue'].replace(0, 1)
    
    if 'cancelledOrders' in aggregated.columns and 'totalOrders' in aggregated.columns:
        aggregated['cancellationRate'] = aggregated['cancelledOrders'] / aggregated['totalOrders'].replace(0, 1)
    
    if 'totalItemsSold' in aggregated.columns and 'totalOrders' in aggregated.columns:
        aggregated['itemsPerOrder'] = aggregated['totalItemsSold'] / aggregated['totalOrders'].replace(0, 1)
    
    if 'totalCosts' in aggregated.columns and 'totalOrders' in aggregated.columns:
        aggregated['costPerOrder'] = aggregated['totalCosts'] / aggregated['totalOrders'].replace(0, 1)
    
    if 'netProfit' in aggregated.columns and 'totalOrders' in aggregated.columns:
        aggregated['profitPerOrder'] = aggregated['netProfit'] / aggregated['totalOrders'].replace(0, 1)
    
    # Drop the weighted columns if they exist
    if weighted_cols:
        aggregated = aggregated.drop(columns=weighted_cols, errors='ignore')
    
    return aggregated


def get_column_safe(df: pd.DataFrame, row, column_name: str, default=0):
    """Safely get a column value, return default if column doesn't exist"""
    if column_name in df.columns:
        return row[column_name]
    return default


def create_revenue_chart(df: pd.DataFrame):
    """Create comprehensive revenue breakdown chart"""
    if df.empty:
        return go.Figure().add_annotation(text="No data available", showarrow=False)
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Revenue Trend', 'Revenue Breakdown', 'Profit Analysis', 'Revenue Distribution'),
        specs=[[{"type": "scatter"}, {"type": "bar"}],
               [{"type": "scatter"}, {"type": "pie"}]]
    )
    
    # Revenue trend over time
    if 'grossRevenue' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['grossRevenue'],
                name='Gross Revenue',
                line=dict(color='#667eea', width=3),
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.1)'
            ),
            row=1, col=1
        )
    
    if 'netRevenue' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['netRevenue'],
                name='Net Revenue',
                line=dict(color='#764ba2', width=3)
            ),
            row=1, col=1
        )
    
    # Revenue breakdown (stacked bar)
    if 'productRevenue' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['productRevenue'],
                name='Product Revenue',
                marker_color='#667eea'
            ),
            row=1, col=2
        )
    
    if 'totalShippingCharged' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['totalShippingCharged'],
                name='Shipping Revenue',
                marker_color='#764ba2'
            ),
            row=1, col=2
        )
    
    # Profit analysis
    if 'grossProfit' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['grossProfit'],
                name='Gross Profit',
                line=dict(color='#10b981', width=3)
            ),
            row=2, col=1
        )
    
    if 'netProfit' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['netProfit'],
                name='Net Profit',
                line=dict(color='#f59e0b', width=3)
            ),
            row=2, col=1
        )
    
    # Revenue distribution (pie chart for latest period)
    latest = df.iloc[-1]
    
    # Build pie chart data dynamically based on available columns
    pie_labels = []
    pie_values = []
    pie_colors = []
    
    revenue_components = [
        ('productRevenue', 'Product', '#667eea'),
        ('totalShippingCharged', 'Shipping', '#764ba2'),
        ('totalGiftWrapRevenue', 'Gift Wrap', '#f59e0b'),
        ('totalTaxCollected', 'Tax', '#10b981'),
        ('totalVatCollected', 'VAT', '#ef4444')
    ]
    
    for col_name, label, color in revenue_components:
        if col_name in df.columns:
            value = get_column_safe(df, latest, col_name, 0)
            if value > 0:  # Only include non-zero values
                pie_labels.append(label)
                pie_values.append(value)
                pie_colors.append(color)
    
    if pie_labels:  # Only add pie chart if we have data
        fig.add_trace(
            go.Pie(
                labels=pie_labels,
                values=pie_values,
                marker=dict(colors=pie_colors)
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text="Revenue & Profit Analysis",
        title_font_size=24,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=1, col=2)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    
    fig.update_yaxes(title_text="Amount ($)", row=1, col=1)
    fig.update_yaxes(title_text="Amount ($)", row=1, col=2)
    fig.update_yaxes(title_text="Profit ($)", row=2, col=1)
    
    return fig


def create_margin_analysis_chart(df: pd.DataFrame):
    """Create margin and efficiency metrics chart"""
    if df.empty:
        return go.Figure().add_annotation(text="No data available", showarrow=False)
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Profit Margins', 'Etsy Fees & Take Home Rate', 'Cost Breakdown', 'Efficiency Ratios'),
        specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Profit margins
    if 'grossMargin' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['grossMargin'] * 100,
                name='Gross Margin %',
                line=dict(color='#10b981', width=3)
            ),
            row=1, col=1
        )
    
    if 'netMargin' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['netMargin'] * 100,
                name='Net Margin %',
                line=dict(color='#f59e0b', width=3)
            ),
            row=1, col=1
        )
    
    # Etsy fees and take home rate
    if 'etsyFeeRate' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['etsyFeeRate'] * 100,
                name='Etsy Fee %',
                line=dict(color='#ef4444', width=3),
                fill='tozeroy'
            ),
            row=1, col=2
        )
    
    if 'takeHomeRate' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['takeHomeRate'] * 100,
                name='Take Home %',
                line=dict(color='#667eea', width=3)
            ),
            row=1, col=2
        )
    
    # Cost breakdown
    if 'totalCost' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['totalCost'],
                name='Product Cost (COGS)',
                marker_color='#667eea'
            ),
            row=2, col=1
        )
    
    if 'actualShippingCost' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['actualShippingCost'],
                name='Shipping Cost',
                marker_color='#764ba2'
            ),
            row=2, col=1
        )
    
    if 'totalEtsyFees' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['totalEtsyFees'],
                name='Etsy Fees',
                marker_color='#ef4444'
            ),
            row=2, col=1
        )
    
    # Efficiency ratios
    if 'markupRatio' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['markupRatio'] * 100,
                name='Markup Ratio %',
                marker_color='#10b981'
            ),
            row=2, col=2
        )
    
    if 'returnOnRevenue' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['returnOnRevenue'] * 100,
                name='Return on Revenue %',
                marker_color='#f59e0b'
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text="Margin & Efficiency Analysis",
        title_font_size=24,
        hovermode='x unified',
        barmode='group'
    )
    
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Margin (%)", row=1, col=1)
    fig.update_yaxes(title_text="Rate (%)", row=1, col=2)
    fig.update_yaxes(title_text="Cost ($)", row=2, col=1)
    fig.update_yaxes(title_text="Ratio (%)", row=2, col=2)
    
    return fig


def create_orders_customers_chart(df: pd.DataFrame):
    """Create orders and customer analytics chart"""
    if df.empty:
        return go.Figure().add_annotation(text="No data available", showarrow=False)
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Order Volume', 'Customer Metrics', 'Order Value Distribution', 'Customer Retention'),
        specs=[[{"type": "bar"}, {"type": "scatter"}],
               [{"type": "box"}, {"type": "scatter"}]]
    )
    
    # Order volume
    if 'totalOrders' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['totalOrders'],
                name='Total Orders',
                marker_color='#667eea',
                text=df['totalOrders'],
                textposition='outside'
            ),
            row=1, col=1
        )
    
    # Customer metrics
    if 'uniqueCustomers' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['uniqueCustomers'],
                name='Unique Customers',
                line=dict(color='#667eea', width=3),
                mode='lines+markers'
            ),
            row=1, col=2
        )
    
    if 'repeatCustomers' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['repeatCustomers'],
                name='Repeat Customers',
                line=dict(color='#764ba2', width=3),
                mode='lines+markers'
            ),
            row=1, col=2
        )
    
    # Order value distribution (box plot)
    if 'averageOrderValue' in df.columns:
        fig.add_trace(
            go.Box(
                x=df['periodStart'].astype(str),
                y=df['averageOrderValue'],
                name='AOV Distribution',
                marker_color='#667eea',
                boxmean='sd'
            ),
            row=2, col=1
        )
    
    # Customer retention rate
    if 'customerRetentionRate' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['customerRetentionRate'] * 100,
                name='Retention Rate %',
                line=dict(color='#10b981', width=3),
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.1)'
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text="Orders & Customer Analytics",
        title_font_size=24,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Orders", row=1, col=1)
    fig.update_yaxes(title_text="Customers", row=1, col=2)
    fig.update_yaxes(title_text="Order Value ($)", row=2, col=1)
    fig.update_yaxes(title_text="Retention Rate (%)", row=2, col=2)
    
    return fig


def create_operational_metrics_chart(df: pd.DataFrame):
    """Create operational metrics chart"""
    if df.empty:
        return go.Figure().add_annotation(text="No data available", showarrow=False)
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Refund Analysis', 'Shipping Performance', 'Inventory Metrics', 'Business Health'),
        specs=[[{"type": "scatter"}, {"type": "bar"}],
               [{"type": "scatter"}, {"type": "indicator"}]]
    )
    
    # Refund analysis
    if 'refundRateByValue' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['refundRateByValue'] * 100,
                name='Refund Rate by Value %',
                line=dict(color='#ef4444', width=3)
            ),
            row=1, col=1
        )
    
    if 'orderRefundRate' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['orderRefundRate'] * 100,
                name='Order Refund Rate %',
                line=dict(color='#f59e0b', width=3)
            ),
            row=1, col=1
        )
    
    # Shipping performance
    if 'shippingRate' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['shippingRate'] * 100,
                name='Shipping Rate %',
                marker_color='#10b981'
            ),
            row=1, col=2
        )
    
    if 'completionRate' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['completionRate'] * 100,
                name='Completion Rate %',
                marker_color='#667eea'
            ),
            row=1, col=2
        )
    
    # Inventory metrics
    if 'inventoryTurnover' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['inventoryTurnover'],
                name='Inventory Turnover',
                line=dict(color='#667eea', width=3),
                mode='lines+markers'
            ),
            row=2, col=1
        )
    
    if 'stockoutRisk' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['stockoutRisk'] * 100,
                name='Stockout Risk %',
                line=dict(color='#ef4444', width=3),
                mode='lines+markers'
            ),
            row=2, col=1
        )
    
    # Business health indicator (latest period)
    latest = df.iloc[-1]
    
    # Calculate health score using available metrics
    health_components = []
    
    if 'netMargin' in df.columns:
        health_components.append((get_column_safe(df, latest, 'netMargin', 0) * 100, 0.3))
    
    if 'refundRateByValue' in df.columns:
        health_components.append(((1 - get_column_safe(df, latest, 'refundRateByValue', 0)) * 100, 0.2))
    
    if 'customerRetentionRate' in df.columns:
        health_components.append((get_column_safe(df, latest, 'customerRetentionRate', 0) * 100, 0.3))
    
    if 'completionRate' in df.columns:
        health_components.append((get_column_safe(df, latest, 'completionRate', 0) * 100, 0.2))
    
    # Calculate weighted health score
    if health_components:
        total_weight = sum(weight for _, weight in health_components)
        health_score = sum(value * weight for value, weight in health_components) / total_weight if total_weight > 0 else 0
    else:
        health_score = 0
    
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=health_score,
            title={'text': "Business Health Score"},
            delta={'reference': 70},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#667eea"},
                'steps': [
                    {'range': [0, 50], 'color': "#fee2e2"},
                    {'range': [50, 70], 'color': "#fef3c7"},
                    {'range': [70, 100], 'color': "#d1fae5"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text="Operational Metrics & Business Health",
        title_font_size=24,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Rate (%)", row=1, col=1)
    fig.update_yaxes(title_text="Rate (%)", row=1, col=2)
    fig.update_yaxes(title_text="Metric Value", row=2, col=1)
    
    return fig


def create_shipping_analysis_chart(df: pd.DataFrame):
    """Create detailed shipping cost analysis chart"""
    if df.empty:
        return go.Figure().add_annotation(text="No data available", showarrow=False)
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Shipping Revenue vs Cost',
            'Shipping Profit/Loss',
            'Shipping Cost Breakdown',
            'Shipping Metrics'
        ),
        specs=[[{"type": "scatter"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "scatter"}]]
    )
    
    # Shipping revenue vs cost
    if 'totalShippingCharged' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['totalShippingCharged'],
                name='Shipping Charged',
                line=dict(color='#10b981', width=3),
                fill='tozeroy'
            ),
            row=1, col=1
        )
    
    if 'actualShippingCost' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['actualShippingCost'],
                name='Actual Shipping Cost',
                line=dict(color='#ef4444', width=3)
            ),
            row=1, col=1
        )
    
    # Shipping profit/loss
    if 'shippingProfit' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['shippingProfit'],
                name='Shipping Profit',
                marker_color=['#10b981' if x >= 0 else '#ef4444' for x in df['shippingProfit']],
                text=df['shippingProfit'].round(2),
                textposition='outside'
            ),
            row=1, col=2
        )
    
    # Shipping cost breakdown (stacked)
    if 'actualShippingCost' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['actualShippingCost'],
                name='FedEx Charges',
                marker_color='#667eea'
            ),
            row=2, col=1
        )
    
    if 'dutyAmount' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['dutyAmount'],
                name='Duty Amount',
                marker_color='#764ba2'
            ),
            row=2, col=1
        )
    
    if 'taxAmount' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['taxAmount'],
                name='Import Tax',
                marker_color='#f59e0b'
            ),
            row=2, col=1
        )
    
    if 'fedexProcessingFee' in df.columns:
        fig.add_trace(
            go.Bar(
                x=df['periodStart'],
                y=df['fedexProcessingFee'],
                name='Processing Fee',
                marker_color='#ef4444'
            ),
            row=2, col=1
        )
    
    # Shipping metrics
    if 'shippingRate' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=df['shippingRate'] * 100,
                name='Shipping Rate %',
                line=dict(color='#667eea', width=3),
                mode='lines+markers'
            ),
            row=2, col=2
        )
    
    # Add average shipping cost per order
    if 'actualShippingCost' in df.columns and 'totalOrders' in df.columns:
        avg_ship_per_order = df['actualShippingCost'] / df['totalOrders'].replace(0, 1)
        fig.add_trace(
            go.Scatter(
                x=df['periodStart'],
                y=avg_ship_per_order,
                name='Avg Ship Cost/Order',
                line=dict(color='#10b981', width=3),
                mode='lines+markers',
                yaxis='y2'
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text="Shipping Cost & Profit Analysis",
        title_font_size=24,
        hovermode='x unified',
        barmode='stack'
    )
    
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Amount ($)", row=1, col=1)
    fig.update_yaxes(title_text="Profit/Loss ($)", row=1, col=2)
    fig.update_yaxes(title_text="Cost ($)", row=2, col=1)
    fig.update_yaxes(title_text="Shipping Rate (%)", row=2, col=2)
    
    # Add secondary y-axis for shipping cost per order
    fig.update_yaxes(title_text="Cost/Order ($)", secondary_y=True, row=2, col=2)
    
    return fig


def create_top_performers_chart(df: pd.DataFrame, metric: str, title: str, n: int = 10):
    """Create top performers chart for listings or products"""
    if df.empty:
        return go.Figure().add_annotation(text="No data available", showarrow=False)
    
    # Group by entity and sum metrics
    if 'listingId' in df.columns:
        entity_col = 'listingId'
        entity_name = 'Listing'
    elif 'sku' in df.columns:
        entity_col = 'sku'
        entity_name = 'SKU'
    else:
        return go.Figure().add_annotation(text="Invalid data structure", showarrow=False)
    
    grouped = df.groupby(entity_col).agg({
        metric: 'sum',
        'totalOrders': 'sum',
        'grossRevenue': 'sum',
        'netProfit': 'sum'
    }).reset_index()
    
    # Sort and get top N
    top_performers = grouped.nlargest(n, metric)
    
    # Convert entity column to string to prevent scientific notation
    if entity_col == 'listingId':
        top_performers[entity_col] = top_performers[entity_col].astype(str)
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=top_performers[metric],
            y=top_performers[entity_col],
            orientation='h',
            marker=dict(
                color=top_performers[metric],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title=metric)
            ),
            text=top_performers[metric].round(2),
            textposition='outside',
            hovertemplate=(
                f'<b>{entity_name} %{{y}}</b><br>' +
                f'{metric}: $%{{x:,.2f}}<br>' +
                'Orders: %{customdata[0]}<br>' +
                'Revenue: $%{customdata[1]:,.2f}<br>' +
                'Profit: $%{customdata[2]:,.2f}<br>' +
                '<extra></extra>'
            ),
            customdata=top_performers[['totalOrders', 'grossRevenue', 'netProfit']].values
        )
    )
    
    fig.update_layout(
        title=title,
        title_font_size=20,
        xaxis_title=f"{metric} ($)",
        yaxis_title=entity_name,
        yaxis=dict(type='category'),  # Force categorical display for Y-axis
        height=500,
        showlegend=False,
        hovermode='closest'
    )
    
    return fig


def display_key_metrics(df: pd.DataFrame):
    """Display key metrics as cards"""
    if df.empty:
        st.warning("No data available for selected period")
        return
    
    # Get latest period data
    latest = df.iloc[-1]
    
    # Calculate period-over-period changes if available
    if len(df) > 1:
        previous = df.iloc[-2]
        
        # Safe calculations with column checks
        if 'grossRevenue' in df.columns:
            revenue_change = ((latest['grossRevenue'] - previous['grossRevenue']) / previous['grossRevenue'] * 100) if previous['grossRevenue'] > 0 else 0
        else:
            revenue_change = 0
            
        if 'netProfit' in df.columns:
            profit_change = ((latest['netProfit'] - previous['netProfit']) / previous['netProfit'] * 100) if previous['netProfit'] > 0 else 0
        else:
            profit_change = 0
            
        if 'totalOrders' in df.columns:
            orders_change = ((latest['totalOrders'] - previous['totalOrders']) / previous['totalOrders'] * 100) if previous['totalOrders'] > 0 else 0
        else:
            orders_change = 0
            
        if 'netMargin' in df.columns:
            margin_change = (latest['netMargin'] - previous['netMargin']) * 100
        else:
            margin_change = 0
    else:
        revenue_change = profit_change = orders_change = margin_change = 0
    
    # Display metrics in columns - only show metrics that exist
    col1, col2, col3, col4 = st.columns(4)
    
    if 'grossRevenue' in df.columns:
        with col1:
            st.metric(
                label="💰 Gross Revenue",
                value=f"${latest['grossRevenue']:,.2f}",
                delta=f"{revenue_change:+.1f}%"
            )
    
    if 'netProfit' in df.columns:
        with col2:
            st.metric(
                label="📈 Net Profit",
                value=f"${latest['netProfit']:,.2f}",
                delta=f"{profit_change:+.1f}%"
            )
    
    if 'totalOrders' in df.columns:
        with col3:
            st.metric(
                label="🛍️ Total Orders",
                value=f"{int(latest['totalOrders']):,}",
                delta=f"{orders_change:+.1f}%"
            )
    
    if 'netMargin' in df.columns:
        with col4:
            st.metric(
                label="💎 Net Margin",
                value=f"{latest['netMargin']*100:.2f}%",
                delta=f"{margin_change:+.2f}%"
            )
    
    # Second row of metrics
    col5, col6, col7, col8 = st.columns(4)
    
    if 'uniqueCustomers' in df.columns:
        with col5:
            st.metric(
                label="👥 Unique Customers",
                value=f"{int(latest['uniqueCustomers']):,}",
                delta=None
            )
    
    if 'customerRetentionRate' in df.columns:
        with col6:
            st.metric(
                label="🔄 Customer Retention",
                value=f"{latest['customerRetentionRate']*100:.1f}%",
                delta=None
            )
    
    if 'averageOrderValue' in df.columns:
        with col7:
            st.metric(
                label="📦 Avg Order Value",
                value=f"${latest['averageOrderValue']:.2f}",
                delta=None
            )
    
    if 'etsyFeeRate' in df.columns:
        with col8:
            st.metric(
                label="🎯 Etsy Fee Rate",
                value=f"{latest['etsyFeeRate']*100:.2f}%",
                delta=None
            )


def main():
    """Main dashboard function"""
    
    # Check authentication first
    if not check_authentication():
        login_page()
        return
    
    # Header with user info
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<h1 class="main-header">📊 Etsy Analytics Dashboard</h1>', unsafe_allow_html=True)
    with col2:
        st.markdown(f"**👤 User:** {st.session_state.get('username', 'Unknown')}")
    
    st.markdown("---")
    
    # Initialize data loader
    loader = DashboardDataLoader()
    
    # Sidebar configuration
    st.sidebar.title("⚙️ Dashboard Settings")
    st.sidebar.markdown("---")
    
    # Logout button in sidebar
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
    
    st.sidebar.markdown("---")
    
    # Report type selection
    report_type = st.sidebar.selectbox(
        "📊 Report Type",
        ["Shop Overview", "Listing Analysis", "Product Analysis", "Comparative Analysis"]
    )
    
    # Period type selection
    period_type = st.sidebar.selectbox(
        "📅 Period Type",
        ["Monthly", "Weekly", "Yearly"]
    )
    
    # Get available date range
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(loader.connect())
        
        min_date, max_date = loop.run_until_complete(loader.get_date_range())
        
        # Date range selection
        st.sidebar.markdown("### 📅 Date Range")
        
        # Show info about data availability
        st.sidebar.info(f"📊 Data available from {min_date.date()} to {max_date.date()}")
        
        # Allow selection up to today to enable preset buttons, will validate after
        from datetime import date as dt_date
        today = dt_date.today()
        
        date_range = st.sidebar.date_input(
            "Select date range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=today,  # Allow up to today for preset buttons
            help=f"Data is available up to {max_date.date()}. Dates beyond this will be adjusted automatically."
        )
        
        # Handle different date_input return types
        if isinstance(date_range, tuple):
            if len(date_range) == 2:
                # Full range selected - validate against max_date
                start_date = datetime.combine(date_range[0], datetime.min.time())
                end_date = datetime.combine(date_range[1], datetime.max.time())
                
                # Ensure end_date doesn't exceed database max_date
                if end_date > max_date:
                    end_date = max_date
                    st.sidebar.warning(f"⚠️ End date adjusted to latest available data: {max_date.date()}")
                
                # Ensure start_date is not after end_date
                if start_date > end_date:
                    start_date = min_date
                    st.sidebar.warning(f"⚠️ Start date adjusted to: {min_date.date()}")
                    
            elif len(date_range) == 1:
                # Only one date selected (user is selecting)
                start_date = datetime.combine(date_range[0], datetime.min.time())
                end_date = datetime.combine(date_range[0], datetime.max.time())
                
                # Ensure dates don't exceed database max_date
                if start_date > max_date:
                    start_date = max_date
                if end_date > max_date:
                    end_date = max_date
                    
                st.sidebar.warning("⚠️ Please select an end date")
            else:
                # Empty tuple (shouldn't happen, but handle it)
                start_date = min_date
                end_date = max_date
        else:
            # Single date object returned
            start_date = datetime.combine(date_range, datetime.min.time())
            end_date = datetime.combine(date_range, datetime.max.time())
            
            # Ensure end_date doesn't exceed database max_date
            if end_date > max_date:
                end_date = max_date
                st.sidebar.warning(f"⚠️ Date adjusted to latest available data: {max_date.date()}")
        
        st.sidebar.markdown("---")
        
        # Additional filters based on report type
        selected_listing = None
        selected_sku = None
        
        if report_type == "Listing Analysis":
            listings = loop.run_until_complete(loader.get_all_listings())
            if listings:
                listing_options = {f"{l.listingId} - {l.title[:50]}": l.listingId for l in listings}
                selected_listing_str = st.sidebar.selectbox("Select Listing", ["All Listings"] + list(listing_options.keys()))
                if selected_listing_str != "All Listings":
                    selected_listing = listing_options[selected_listing_str]
        
        elif report_type == "Product Analysis":
            skus = loop.run_until_complete(loader.get_all_skus())
            if skus:
                selected_sku = st.sidebar.selectbox("Select SKU", ["All SKUs"] + skus)
                if selected_sku == "All SKUs":
                    selected_sku = None
        
        # Fetch data based on report type
        if report_type == "Shop Overview":
            reports = loop.run_until_complete(
                loader.get_shop_reports(period_type, start_date, end_date)
            )
            df = convert_reports_to_dataframe(reports)
            
        elif report_type == "Listing Analysis":
            reports = loop.run_until_complete(
                loader.get_listing_reports(period_type, start_date, end_date, selected_listing)
            )
            df = convert_reports_to_dataframe(reports)
            
            # Debug: Show query info if no data
            if df.empty and selected_listing:
                st.sidebar.error(f"🔍 No data found for Listing ID: {selected_listing}")
                st.sidebar.info(f"📅 Date range: {start_date.date()} to {end_date.date()}")
                st.sidebar.info(f"📊 Period type: {period_type}")
            
            # If "All Listings" selected, aggregate by period for cleaner visualization
            if selected_listing is None:
                df = aggregate_reports_by_period(df)
            
        elif report_type == "Product Analysis":
            reports = loop.run_until_complete(
                loader.get_product_reports(period_type, start_date, end_date, selected_sku)
            )
            df = convert_reports_to_dataframe(reports)
            
            # If "All SKUs" selected, aggregate by period for cleaner visualization
            if selected_sku is None:
                df = aggregate_reports_by_period(df)
            
        else:  # Comparative Analysis
            shop_reports = loop.run_until_complete(
                loader.get_shop_reports(period_type, start_date, end_date)
            )
            listing_reports = loop.run_until_complete(
                loader.get_listing_reports(period_type, start_date, end_date)
            )
            product_reports = loop.run_until_complete(
                loader.get_product_reports(period_type, start_date, end_date)
            )
            df = convert_reports_to_dataframe(shop_reports)
        
        # Display dashboard content
        if not df.empty:
            # Key metrics
            st.markdown("## 📊 Key Metrics")
            display_key_metrics(df)
            st.markdown("---")
            
            # Tabs for different visualizations
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "💰 Revenue & Profit",
                "📊 Margins & Efficiency",
                "🛍️ Orders & Customers",
                "⚙️ Operations",
                "🚚 Shipping Analysis",
                "📈 Top Performers"
            ])
            
            with tab1:
                st.plotly_chart(create_revenue_chart(df), width='stretch')
                
                # Revenue summary table
                st.markdown("### 📋 Revenue Summary")
                
                # Build summary with only available columns
                summary_cols = []
                summary_labels = []
                summary_formats = {}
                
                col_mapping = {
                    'periodStart': ('Period', None),
                    'grossRevenue': ('Gross Revenue', '${:,.2f}'),
                    'netRevenue': ('Net Revenue', '${:,.2f}'),
                    'productRevenue': ('Product Revenue', '${:,.2f}'),
                    'totalShippingCharged': ('Shipping Revenue', '${:,.2f}'),
                    'totalEtsyFees': ('Etsy Fees', '${:,.2f}'),
                    'netProfit': ('Net Profit', '${:,.2f}')
                }
                
                for col, (label, fmt) in col_mapping.items():
                    if col in df.columns:
                        summary_cols.append(col)
                        summary_labels.append(label)
                        if fmt:
                            summary_formats[label] = fmt
                
                if summary_cols:
                    summary_df = df[summary_cols].copy()
                    summary_df.columns = summary_labels
                    if 'Period' in summary_df.columns:
                        summary_df['Period'] = summary_df['Period'].dt.strftime('%Y-%m-%d')
                    st.dataframe(summary_df.style.format(summary_formats), width='stretch')
            
            with tab2:
                st.plotly_chart(create_margin_analysis_chart(df), width='stretch')
                
                # Margin summary
                st.markdown("### 📋 Margin Summary")
                
                # Build margin summary with only available columns
                margin_cols = []
                margin_labels = []
                margin_formats = {}
                
                margin_mapping = {
                    'periodStart': ('Period', None),
                    'grossMargin': ('Gross Margin', '{:.2%}'),
                    'netMargin': ('Net Margin', '{:.2%}'),
                    'markupRatio': ('Markup Ratio', '{:.2%}'),
                    'etsyFeeRate': ('Etsy Fee Rate', '{:.2%}'),
                    'takeHomeRate': ('Take Home Rate', '{:.2%}')
                }
                
                for col, (label, fmt) in margin_mapping.items():
                    if col in df.columns:
                        margin_cols.append(col)
                        margin_labels.append(label)
                        if fmt:
                            margin_formats[label] = fmt
                
                if margin_cols:
                    margin_df = df[margin_cols].copy()
                    margin_df.columns = margin_labels
                    if 'Period' in margin_df.columns:
                        margin_df['Period'] = margin_df['Period'].dt.strftime('%Y-%m-%d')
                    st.dataframe(margin_df.style.format(margin_formats), width='stretch')
            
            with tab3:
                st.plotly_chart(create_orders_customers_chart(df), width='stretch')
                
                # Customer insights
                st.markdown("### 👥 Customer Insights")
                col1, col2, col3 = st.columns(3)
                
                total_customers = df['uniqueCustomers'].sum() if 'uniqueCustomers' in df.columns else 0
                total_repeat = df['repeatCustomers'].sum() if 'repeatCustomers' in df.columns else 0
                avg_retention = df['customerRetentionRate'].mean() if 'customerRetentionRate' in df.columns else 0
                
                with col1:
                    st.metric("Total Unique Customers", f"{int(total_customers):,}")
                with col2:
                    st.metric("Total Repeat Customers", f"{int(total_repeat):,}")
                with col3:
                    st.metric("Avg Retention Rate", f"{avg_retention*100:.2f}%")
            
            with tab4:
                st.plotly_chart(create_operational_metrics_chart(df), width='stretch')
                
                # Operational KPIs
                st.markdown("### 📊 Operational KPIs")
                col1, col2, col3, col4 = st.columns(4)
                
                avg_ship_rate = df['shippingRate'].mean() if 'shippingRate' in df.columns else 0
                avg_completion = df['completionRate'].mean() if 'completionRate' in df.columns else 0
                avg_refund_rate = df['refundRateByValue'].mean() if 'refundRateByValue' in df.columns else 0
                avg_cancel_rate = df['cancellationRate'].mean() if 'cancellationRate' in df.columns else 0
                
                with col1:
                    st.metric("Avg Shipping Rate", f"{avg_ship_rate*100:.2f}%")
                with col2:
                    st.metric("Avg Completion Rate", f"{avg_completion*100:.2f}%")
                with col3:
                    st.metric("Avg Refund Rate", f"{avg_refund_rate*100:.2f}%")
                with col4:
                    st.metric("Avg Cancel Rate", f"{avg_cancel_rate*100:.2f}%")
            
            with tab5:
                st.plotly_chart(create_shipping_analysis_chart(df), width='stretch')
                
                # Shipping metrics
                st.markdown("### 🚚 Shipping Metrics Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                total_ship_charged = df['totalShippingCharged'].sum() if 'totalShippingCharged' in df.columns else 0
                total_ship_cost = df['actualShippingCost'].sum() if 'actualShippingCost' in df.columns else 0
                total_ship_profit = df['shippingProfit'].sum() if 'shippingProfit' in df.columns else 0
                avg_ship_margin = (total_ship_profit / total_ship_charged * 100) if total_ship_charged > 0 else 0
                
                with col1:
                    st.metric("Total Shipping Charged", f"${total_ship_charged:,.2f}")
                with col2:
                    st.metric("Total Shipping Cost", f"${total_ship_cost:,.2f}")
                with col3:
                    st.metric("Total Shipping Profit", f"${total_ship_profit:,.2f}")
                with col4:
                    st.metric("Shipping Margin", f"{avg_ship_margin:.2f}%")
            
            with tab6:
                if report_type == "Listing Analysis":
                    listing_df = convert_reports_to_dataframe(
                        loop.run_until_complete(loader.get_listing_reports(period_type, start_date, end_date))
                    )
                    if not listing_df.empty:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(
                                create_top_performers_chart(listing_df, 'netProfit', 'Top 10 Listings by Net Profit'),
                                width='stretch'
                            )
                        with col2:
                            st.plotly_chart(
                                create_top_performers_chart(listing_df, 'grossRevenue', 'Top 10 Listings by Revenue'),
                                width='stretch'
                            )
                
                elif report_type == "Product Analysis":
                    product_df = convert_reports_to_dataframe(
                        loop.run_until_complete(loader.get_product_reports(period_type, start_date, end_date))
                    )
                    if not product_df.empty:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(
                                create_top_performers_chart(product_df, 'netProfit', 'Top 10 Products by Net Profit'),
                                width='stretch'
                            )
                        with col2:
                            st.plotly_chart(
                                create_top_performers_chart(product_df, 'totalQuantitySold', 'Top 10 Products by Units Sold'),
                                width='stretch'
                            )
                else:
                    st.info("Top performers analysis is available in Listing Analysis and Product Analysis views.")
            
            # Download data section
            st.markdown("---")
            st.markdown("## 📥 Download Data")
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📊 Download as CSV",
                    data=csv,
                    file_name=f"{report_type.lower().replace(' ', '_')}_{period_type.lower()}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                st.download_button(
                    label="📋 Download as JSON",
                    data=df.to_json(orient='records', date_format='iso'),
                    file_name=f"{report_type.lower().replace(' ', '_')}_{period_type.lower()}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
        
        else:
            st.warning("⚠️ No data available for the selected filters. Please adjust your selection.")
            st.info("💡 Make sure you have generated reports using the reportsv4_optimized.py script first.")
        
        # Cleanup
        loop.run_until_complete(loader.disconnect())
        loop.close()
    
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.info("💡 Make sure your database connection is configured correctly and reports have been generated.")
        import traceback
        st.code(traceback.format_exc())
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>📊 Etsy Analytics Dashboard v1.1 | Built with Streamlit & Plotly</p>
        <p>💡 For best results, ensure your reports are up to date</p>
        <p>🔒 Secure access • Protected business data</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
