# 📊 Etsy Analytics Dashboard - User Guide

## 🎯 Overview

The Etsy Analytics Dashboard is a powerful, interactive web-based visualization tool that provides comprehensive insights into your e-commerce business performance. Built with Streamlit and Plotly, it offers real-time analytics across revenue, profits, customers, operations, and more.

**🔒 Security First:** The dashboard now includes authentication to protect your sensitive business data from unauthorized access.

## ✨ Key Features

### 🔐 **Security & Authentication**

- Login protection with username/password
- Session-based authentication
- Configurable credentials via environment variables
- Secure logout functionality
- SHA-256 password hashing

### 📈 **Multi-Level Reporting**

- **Shop Overview**: Complete business performance metrics
- **Listing Analysis**: Individual product listing insights
- **Product Analysis**: SKU-level performance tracking
- **Comparative Analysis**: Cross-entity comparisons

### 💰 **Financial Analytics**

- Revenue breakdown (Product, Shipping, Fees, Taxes)
- Profit analysis (Gross & Net Profit)
- Margin tracking (Gross Margin, Net Margin)
- Etsy fee calculations and impact
- Shipping cost analysis with profit/loss

### 👥 **Customer Intelligence**

- Unique vs. Repeat customers
- Customer retention rates
- Customer Lifetime Value (CLV)
- Average Order Value (AOV)
- Orders per customer

### ⚙️ **Operational Insights**

- Order fulfillment rates
- Shipping performance
- Refund analytics
- Cancellation tracking
- Inventory turnover
- Business health score

### 📊 **Advanced Visualizations**

- Interactive time-series charts
- Profit margin trends
- Cost breakdown analysis
- Top performer rankings
- Distribution plots
- Real-time KPI gauges

## 🚀 Installation & Setup

### Prerequisites

1. **Python 3.8+** installed
2. **Database with generated reports** (run `reportsv4_optimized.py` first)
3. **Environment variables** configured (`.env` file with `DATABASE_URL`)
4. **🔐 Authentication credentials** configured (see Step 1 below)

### Step 1: Configure Authentication (NEW!)

**Option A: Automated Setup (Recommended)**

```bash
# Run the interactive setup script
python setup_auth.py
```

**Option B: Manual Setup**

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set your credentials
nano .env  # or use any text editor
```

Set these variables in `.env`:

```env
DASHBOARD_USERNAME=your_username
DASHBOARD_PASSWORD=your_secure_password
```

**⚠️ IMPORTANT:** Change the default credentials immediately!

- Default username: `admin`
- Default password: `changeme123`

For detailed security setup, see `SECURITY_GUIDE.md`

### Step 2: Install Dependencies

```bash
# Navigate to project directory
cd /Users/ahmetbayram/Documents/projects/reports_generation

# Install dashboard requirements
pip install -r requirements_dashboard.txt
```

### Step 3: Generate Reports (if not done)

```bash
# Generate all analytics reports first
python reportsv4_optimized.py --cost-file cost.csv

# Or with clean regeneration
python reportsv4_optimized.py --clean-reports
```

### Step 4: Launch Dashboard

```bash
# Start the Streamlit dashboard
streamlit run dashboard.py
```

The dashboard will automatically open in your default web browser at `http://localhost:8501`

**You'll be prompted to login with your configured credentials.**

## 📖 How to Use

### 1. **Select Report Type**

In the sidebar, choose your analysis focus:

- **Shop Overview**: See overall business performance
- **Listing Analysis**: Analyze specific product listings
- **Product Analysis**: Deep dive into SKU performance
- **Comparative Analysis**: Compare multiple entities

### 2. **Choose Period Type**

Select the time granularity:

- **Yearly**: Annual trends and year-over-year comparisons
- **Monthly**: Month-by-month performance (recommended)
- **Weekly**: Detailed weekly tracking

### 3. **Set Date Range**

Use the date picker to select:

- Start date
- End date
- Available range based on your order history

### 4. **Apply Filters** (Optional)

For specific analysis:

- **Listing Analysis**: Select individual listing or view all
- **Product Analysis**: Select specific SKU or view all

### 5. **Explore Visualizations**

Navigate through tabs:

#### **💰 Revenue & Profit**

- Revenue trend over time
- Revenue breakdown by component
- Gross vs. Net profit analysis
- Revenue distribution pie chart

#### **📊 Margins & Efficiency**

- Profit margin trends (Gross & Net)
- Etsy fee impact
- Cost breakdown (COGS, Shipping, Fees)
- Efficiency ratios (Markup, ROI)

#### **🛍️ Orders & Customers**

- Order volume tracking
- Customer acquisition & retention
- Order value distribution
- Customer lifecycle metrics

#### **⚙️ Operations**

- Refund rate analysis
- Shipping & completion rates
- Inventory turnover
- Business health score gauge

#### **🚚 Shipping Analysis**

- Shipping revenue vs. cost
- Shipping profit/loss by period
- Cost breakdown (FedEx, Duty, Tax, Fees)
- Shipping efficiency metrics

#### **📈 Top Performers**

- Best performing listings (by profit/revenue)
- Top selling products (by units/revenue)
- Performance rankings and comparisons

### 6. **Download Data**

Export your analysis:

- **CSV format**: For Excel/spreadsheet analysis
- **JSON format**: For further processing or API integration

## 💡 Dashboard Insights Explained

### Key Metrics Cards

At the top of the dashboard, you'll see:

1. **💰 Gross Revenue**: Total revenue from all sources

   - Includes: Product sales + Shipping + Taxes + Fees
   - Delta: % change vs. previous period

2. **📈 Net Profit**: Final profit after all costs and fees

   - Formula: `Net Revenue - Total Costs - Etsy Fees - Refunds`
   - Delta: % change vs. previous period

3. **🛍️ Total Orders**: Number of completed orders

   - Excludes: Cancelled orders
   - Delta: % change vs. previous period

4. **💎 Net Margin**: Profit as % of revenue
   - Formula: `(Net Profit / Gross Revenue) × 100`
   - Delta: Percentage point change vs. previous period

### Understanding Financial Metrics

#### Revenue Metrics

- **Gross Revenue**: What customers paid (total)
- **Net Revenue**: After Etsy fees & taxes collected
- **Product Revenue**: Sales revenue excluding shipping/fees
- **Take Home Rate**: % of gross revenue you actually keep

#### Cost Metrics

- **COGS (Cost of Goods Sold)**: Product manufacturing costs
- **Actual Shipping Cost**: FedEx charges + duties + taxes
- **Etsy Fees**: Transaction + Processing fees
- **Total Cost with Shipping**: All costs combined

#### Profit Metrics

- **Gross Profit**: Revenue - COGS - Shipping Costs
- **Net Profit**: Gross Profit - Etsy Fees - Refunds
- **Gross Margin**: Gross Profit / Revenue
- **Net Margin**: Net Profit / Revenue

#### Shipping Metrics

- **Shipping Charged**: What customers paid for shipping
- **Actual Shipping Cost**: What you paid to carriers
- **Shipping Profit**: Charged - Actual Cost (can be negative!)
- **Duty Amount**: US customs duties (COST to you)
- **Tax Amount**: US import taxes (COST to you)
- **FedEx Processing Fee**: Carrier processing charges

### Business Health Score

The gauge shows overall business health (0-100):

- **0-50 (Red)**: Critical issues need attention
- **50-70 (Yellow)**: Room for improvement
- **70-100 (Green)**: Healthy business performance

Calculated from:

- Net Margin (30% weight)
- Refund Rate (20% weight)
- Customer Retention (30% weight)
- Completion Rate (20% weight)

## 🎨 Customization Options

### Changing Date Ranges

- Use sidebar date picker for custom ranges
- Dashboard automatically adjusts all visualizations

### Filtering Data

- **By Listing**: Focus on specific product listings
- **By SKU**: Analyze individual product variants
- **By Period**: Compare different time granularities

### Exporting Reports

- **CSV**: Open in Excel for custom analysis
- **JSON**: Integrate with other tools/APIs

## ⚠️ Troubleshooting

### Dashboard Won't Start

```bash
# Check Streamlit installation
streamlit --version

# Reinstall if needed
pip install --upgrade streamlit
```

### "No data available" Message

- Ensure you've run `reportsv4_optimized.py` to generate reports
- Check database connection (`.env` file)
- Verify date range has data

### Database Connection Error

- Confirm `DATABASE_URL` in `.env` file
- Test connection: `python -c "from prisma import Prisma; import asyncio; asyncio.run(Prisma().connect())"`

### Slow Loading

- Large date ranges may take longer
- Try narrower date ranges or fewer periods
- Consider using Weekly view for detailed analysis

### Charts Not Displaying

- Clear browser cache
- Update Plotly: `pip install --upgrade plotly`
- Try different browser

## 🔧 Advanced Tips

### Best Practices

1. **Regular Updates**: Regenerate reports weekly for current data
2. **Comparative Analysis**: Use period-over-period comparisons
3. **Top Performers**: Identify and focus on high-profit items
4. **Cost Monitoring**: Watch shipping profit/loss trends
5. **Customer Metrics**: Track retention for business health

### Performance Optimization

1. **Narrow Date Ranges**: Use specific periods for faster loading
2. **Monthly Period**: Best balance of detail vs. performance
3. **Specific Filters**: Use listing/SKU filters when possible
4. **Regular Cleanup**: Archive old reports if database grows large

### Data Accuracy

- **Currency**: Ensure all orders in same currency (USD)
- **Cost Data**: Keep `cost.csv` updated with current costs
- **Shipping Costs**: Verify FedEx pricing CSVs are current
- **Etsy Fees**: Update fee rates if Etsy changes structure

## 📊 Use Cases

### Weekly Business Review

1. Set period type to "Weekly"
2. Select last 4-8 weeks
3. Review "Operations" tab for fulfillment issues
4. Check "Shipping Analysis" for cost trends

### Monthly Financial Planning

1. Set period type to "Monthly"
2. Select current year
3. Review "Revenue & Profit" for trends
4. Check "Margins & Efficiency" for optimization

### Product Performance Analysis

1. Switch to "Product Analysis"
2. Select "Monthly" period
3. Navigate to "Top Performers" tab
4. Identify best/worst performing SKUs

### Seasonal Planning

1. Set period to "Monthly" or "Weekly"
2. Select full year date range
3. Review "Revenue & Profit" trends
4. Identify peak seasons and plan inventory

## 🆘 Support & Resources

### Documentation

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Python Documentation](https://plotly.com/python/)
- [Prisma Python Client](https://prisma-client-py.readthedocs.io/)

### Common Issues

- Check `ARCHITECTURE.md` for system design
- Review `DATABASE_CONNECTION_FIX.md` for connection issues
- See `DASHBOARD_INDEPENDENCE_SUMMARY.md` for independence notes

### Getting Help

1. Check error messages in terminal
2. Verify all dependencies installed
3. Ensure database has data
4. Review this guide's troubleshooting section

## 🎯 Next Steps

1. **Generate Fresh Reports**: Run `reportsv4_optimized.py --clean-reports`
2. **Explore Dashboard**: Launch with `streamlit run dashboard.py`
3. **Analyze Data**: Use filters and tabs to explore insights
4. **Export Findings**: Download CSV/JSON for further analysis
5. **Take Action**: Use insights to optimize your business!

---

**Dashboard Version**: 1.0  
**Last Updated**: 2025-01-07  
**Requires**: Python 3.8+, PostgreSQL Database, Generated Reports
