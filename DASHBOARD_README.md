# E-commerce Analytics Dashboard

A **secure, real-time** Streamlit dashboard with authentication that calculates analytics on-the-fly from your PostgreSQL database.

## 🔒 **NEW: Secure Authentication**

**The dashboard now requires login to protect your sensitive business data!**

### Quick Setup

```bash
# Run automated setup
python setup_auth.py

# Or manual setup
cp .env.example .env
nano .env  # Edit credentials
```

**Default credentials (⚠️ CHANGE IMMEDIATELY!):**

- Username: `admin`
- Password: `changeme123`

📖 **Full Documentation:**

- [Quick Start](AUTHENTICATION_QUICKSTART.md) - 2-minute setup
- [Security Guide](SECURITY_GUIDE.md) - Complete security docs
- [Usage Guide](DASHBOARD_USAGE_GUIDE.md) - Full manual

### Security Features

- 🔐 Login protection with username/password
- 🔒 SHA-256 password hashing
- 🎫 Session-based authentication
- 🚪 Secure logout functionality
- 🛡️ Environment variable configuration

---

## 🔥 Important: How This Dashboard Works

**This dashboard does NOT fetch pre-generated reports from the database!**

Instead, it:

- ✅ Fetches **orders** data directly from the database
- ✅ Fetches **listings** data for SKU mappings
- ✅ **Calculates all metrics in real-time** using the analytics engine
- ✅ Shows **latest/live data** - always up to date
- ❌ Does NOT depend on the reports generation script (`reportsv4_optimized.py`) being run
- ❌ Does NOT read from `shop_reports`, `listing_reports`, or `product_reports` tables

**The reports script (`reportsv4_optimized.py`)** saves calculated metrics to the database for historical tracking and batch analysis.

**The dashboard** calculates metrics fresh every time you view them, giving you real-time insights.

## 🌟 Features

### 📊 Shop Overview

- **Financial Metrics**: Gross revenue, net revenue, gross profit, net profit, margins
- **Cost Analysis**: COGS, shipping costs, duties, taxes, Etsy fees breakdown
- **Profit Waterfall**: Visual breakdown from revenue to net profit
- **Time Series**: Daily trends for revenue, profit, orders, and costs
- **Top Performers**: Identify best-selling products by profit, revenue, or orders

### 🏷️ Listing Analysis

- Deep dive into individual listing performance
- Listing-specific financial metrics
- Time series analysis for listings
- Shipping cost analysis per listing

### 📦 Product Analysis

- Individual SKU performance tracking
- Product-level profitability analysis
- Shipping costs per product
- Time series trends for products

### ⚖️ Period Comparison

- Compare two time periods side-by-side
- Track growth/decline in key metrics
- Percentage change calculations

### 📦 Shipping Analytics

- Shipping charged vs actual costs
- Shipping profit/loss tracking
- US duties and import taxes breakdown
- FedEx processing fees

### 👥 Customer Insights

- Unique vs repeat customers
- Customer retention rate
- Customer lifetime value (CLV)
- Revenue per customer

### ↩️ Refund Analysis

- Total refund amounts and rates
- Etsy fees lost on refunds
- Order-level refund metrics

## 🚀 Installation

1. **Install dependencies:**

```bash
pip install -r requirements_dashboard.txt
```

2. **Ensure your database is set up:**

   - Make sure your PostgreSQL database is running
   - Ensure Prisma migrations are applied
   - Verify all CSV files are in the project directory

3. **Required CSV files** (should be in the same directory):
   - `cost.csv`
   - `all_products_desi.csv`
   - `fedex_country_code_and_zone_number.csv`
   - `fedex_price_per_kg_for_zones.csv`
   - `us_fedex_desi_and_price.csv`

## 📊 Usage

### Start the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your default web browser at `http://localhost:8501`

### Navigation

**Sidebar Controls:**

- **View Mode**: Select between Shop Overview, Listing Analysis, Product Analysis, or Comparison
- **Date Range**: Choose preset ranges or custom dates
  - Last 7 Days
  - Last 30 Days
  - Last 90 Days
  - This Month
  - Last Month
  - This Year
  - Custom range
- **Filters**: Select specific listings or products when in those views

### View Modes

#### 1. Shop Overview

- View all shop-wide metrics
- Financial overview with key metrics
- Shipping cost analysis
- Multiple tabs for:
  - Charts (profit waterfall, cost breakdown)
  - Orders (order metrics, top performers)
  - Customers (customer analytics)
  - Refunds (refund analysis)

#### 2. Listing Analysis

- Select a listing ID from the dropdown
- View all metrics specific to that listing
- Time series analysis for the listing
- Shipping costs for that listing

#### 3. Product Analysis

- Select a SKU from the dropdown
- View product-specific performance
- Profitability analysis
- Time series trends

#### 4. Comparison Mode

- Compare two different time periods
- See percentage changes in key metrics
- Identify growth trends

## 📈 Key Metrics Explained

### Revenue Metrics

- **Gross Revenue**: Total amount customers paid (grand_total from orders)
- **Net Revenue**: Revenue after Etsy fees and taxes
- **Product Revenue**: Revenue from product sales only (excluding shipping)

### Cost Metrics

- **COGS**: Cost of goods sold from cost.csv
- **Actual Shipping Cost**: Real FedEx charges we pay
- **Duties & Taxes**: US customs duties and import taxes
- **Etsy Fees**: Transaction fees (6.5%) + processing fees (3% + $0.25)

### Profit Metrics

- **Gross Profit**: Net Revenue - Total Costs (COGS + Shipping + Duties/Taxes)
- **Net Profit**: Gross Profit - Refunds - Etsy fees retained on refunds
- **Gross Margin**: Gross Profit / Gross Revenue
- **Net Margin**: Net Profit / Gross Revenue

### Shipping Metrics

- **Shipping Charged**: Amount customers paid for shipping
- **Actual Shipping Cost**: Real FedEx costs
- **Shipping Profit**: Charged - Actual (can be negative)
- **Duty Amount**: US customs duties paid
- **Tax Amount**: US import taxes paid

## 🎨 Features

### Interactive Charts

- **Waterfall Chart**: Visualize the flow from revenue to net profit
- **Pie Chart**: Cost distribution breakdown
- **Time Series**: Daily trends with multiple metrics
- **Bar Charts**: Top performing products

### Real-time Data

- Connects directly to your PostgreSQL database
- **Calculates metrics on-the-fly from orders and listings data**
- **Does NOT use pre-generated reports**
- Always shows current, live data with zero lag

### Responsive Design

- Wide layout for better visualization
- Metric cards with clear formatting
- Color-coded positive/negative values

## 🔧 Customization

### Modify Date Presets

Edit the `date_preset` section in `dashboard.py`:

```python
date_preset = st.selectbox(
    "Quick Select",
    ["Custom", "Last 7 Days", "Your Custom Range", ...]
)
```

### Add New Metrics

Extend the rendering methods in the `DashboardApp` class:

```python
def render_your_custom_metric(self, metrics: Dict):
    st.subheader("Your Metric")
    value = metrics.get('your_field', 0)
    st.metric("Label", self.format_currency(value))
```

### Change Color Schemes

Modify Plotly color schemes in chart methods:

```python
color_discrete_sequence=px.colors.qualitative.Pastel
```

## 🐛 Troubleshooting

### "Failed to connect to database"

- Verify your database is running
- Check DATABASE_URL in your environment
- Ensure Prisma client is generated: `prisma generate`

### "No data available"

- Check that you have orders in the selected date range
- Verify CSV files are present and correctly formatted
- Ensure migrations are applied: `prisma migrate dev`

### Slow Performance

- The dashboard limits SKU analysis to 50 products for performance
- Reduce date range for time series analysis
- Ensure database indexes are created

### Missing CSV Files

```
FileNotFoundError: [Errno 2] No such file or directory: 'cost.csv'
```

- Ensure all required CSV files are in the same directory as dashboard.py
- Check file names match exactly (case-sensitive)

## 📝 Notes

- **First Load**: The initial connection may take a few seconds as it loads all data
- **Data Caching**: The analytics engine uses LRU caching for performance
- **Currency**: All amounts are displayed in USD
- **Time Zone**: Uses local system time zone

## 🔒 Security

- Dashboard runs locally on your machine
- No data is sent to external servers
- Direct database connection (ensure proper security)

## 🆘 Support

For issues or questions:

1. Check the troubleshooting section
2. Review the main analytics engine logs
3. Verify database connection and data integrity

## 📄 License

This dashboard is part of your e-commerce analytics system.

---

**Happy Analyzing! 📊**
