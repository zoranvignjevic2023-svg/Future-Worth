from io import BytesIO
import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import altair as alt

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Future Worth",
    page_icon="💰",
    layout="wide"
)

# ======================================================
# FORMATTERS
# ======================================================
def format_large_number(value):
    try:
        value = float(value)
    except:
        return "N/A"

    abs_value = abs(value)

    if abs_value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:,.2f} trillion"
    elif abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f} billion"
    elif abs_value >= 1_000_000:
        return f"{value / 1_000_000:,.2f} million"
    elif abs_value >= 1_000:
        return f"{value / 1_000:,.2f} thousand"
    else:
        return f"{value:,.2f}"

def format_dollar_large(value):
    return "$" + format_large_number(value)

# ======================================================
# THEME
# ======================================================
st.markdown("""
<style>
.stApp {
    background-color: #0C2340;
    color: white;
}

[data-testid="stSidebar"] {
    background-color: #081B33;
}

.block-container {
    padding-top: 2rem;
}

.hero {
    background: linear-gradient(135deg, #0C2340, #002B5C);
    padding: 35px;
    border-radius: 25px;
    border: 2px solid #FFC72C;
    margin-bottom: 25px;
}

.hero-title {
    font-size: 58px;
    font-weight: 900;
    color: #FFC72C;
}

.hero-subtitle {
    font-size: 19px;
    color: #E2E8F0;
}

[data-testid="stMetric"] {
    background-color: #002B5C;
    padding: 18px;
    border-radius: 18px;
    border: 1px solid #FFC72C;
}

.card {
    background-color: #002B5C;
    padding: 20px;
    border-radius: 18px;
    border: 1px solid #FFC72C;
    margin-bottom: 15px;
}

.good {
    color: #22C55E;
    font-weight: 900;
    font-size: 28px;
}

.bad {
    color: #EF4444;
    font-weight: 900;
    font-size: 28px;
}

.gold {
    color: #FFC72C;
    font-weight: 900;
    font-size: 28px;
}

h1, h2, h3 {
    color: white;
}

.stSlider [role="slider"] {
    background-color: #FFC72C !important;
    border: 2px solid #FFC72C !important;
}

.stSlider div[data-testid="stThumbValue"] {
    color: #FFC72C !important;
}

div[data-testid="stSliderTickBar"] {
    background: transparent !important;
}

button[role="tab"][aria-selected="true"] {
    color: #FFC72C !important;
    border-bottom: 3px solid #FFC72C !important;
}

button[role="tab"] {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# HEADER
# ======================================================
st.markdown("""
<div class="hero">
    <div class="hero-title">💰 Future Worth</div>
    <div class="hero-subtitle">
        A blue-and-gold DCF valuation dashboard with live market data, Excel export,
        peer comparisons, price charts, and Bear / Base / Bull scenarios.
    </div>
</div>
""", unsafe_allow_html=True)

# ======================================================
# TICKER INPUT
# ======================================================
st.markdown("## Start a Valuation")

ticker = st.text_input(
    "Enter Stock Ticker",
    value="AAPL",
    placeholder="Example: AAPL, MSFT, TSLA, NVDA"
).upper()

if ticker == "":
    st.warning("Enter a ticker to begin.")
    st.stop()

# ======================================================
# MARKET DATA
# ======================================================
try:
    stock = yf.Ticker(ticker)
    info = stock.info

    company_name = info.get("longName", ticker)
    price = info.get("currentPrice", 0)
    revenue = info.get("totalRevenue", 1_000_000_000)
    shares = info.get("sharesOutstanding", 1_000_000_000)
    debt = info.get("totalDebt", 0)
    cash = info.get("totalCash", 0)
    market_cap = info.get("marketCap", price * shares if price else 0)

except Exception:
    st.warning("Could not pull live company data. Using demo values.")
    stock = None
    info = {}
    company_name = ticker
    price = 0
    revenue = 1_000_000_000
    shares = 1_000_000_000
    debt = 0
    cash = 0
    market_cap = 0

# ======================================================
# SIDEBAR INPUTS
# ======================================================
st.sidebar.title("DCF Controls")

mode = st.sidebar.radio(
    "Input Mode",
    ["Simple Mode", "Advanced Mode"]
)

growth = st.sidebar.slider("Revenue Growth (%)", -5.0, 25.0, 5.0, 0.5) / 100
wacc = st.sidebar.slider("WACC (%)", 5.0, 20.0, 10.0, 0.5) / 100
terminal_growth = st.sidebar.slider("Terminal Growth (%)", 0.0, 5.0, 2.5, 0.25) / 100
years = st.sidebar.slider("Projection Years", 3, 10, 5)

if mode == "Simple Mode":
    ebit_margin = info.get("operatingMargins", 0.20)

    if ebit_margin is None or ebit_margin <= 0:
        ebit_margin = 0.20

    tax_rate = 0.21
    reinvestment_rate = 0.25

else:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Advanced Inputs")

    revenue = st.sidebar.number_input("Revenue", value=float(revenue), min_value=0.0)
    ebit_margin = st.sidebar.slider("EBIT Margin (%)", 0.0, 50.0, 20.0, 0.5) / 100
    tax_rate = st.sidebar.slider("Tax Rate (%)", 0.0, 40.0, 21.0, 0.5) / 100
    reinvestment_rate = st.sidebar.slider("Reinvestment Rate (%)", 0.0, 100.0, 25.0, 1.0) / 100
    debt = st.sidebar.number_input("Debt", value=float(debt), min_value=0.0)
    cash = st.sidebar.number_input("Cash", value=float(cash), min_value=0.0)
    shares = st.sidebar.number_input("Shares Outstanding", value=float(shares), min_value=1.0)

if wacc <= terminal_growth:
    st.error("WACC must be greater than terminal growth.")
    st.stop()

if shares <= 0:
    st.error("Shares outstanding must be greater than zero.")
    st.stop()

# ======================================================
# DCF FUNCTION
# ======================================================
def run_dcf(revenue, growth, ebit_margin, tax_rate, reinvestment_rate,
            wacc, terminal_growth, years, debt, cash, shares):

    data = []
    rev = revenue

    for year in range(1, years + 1):
        rev = rev * (1 + growth)
        ebit = rev * ebit_margin
        nopat = ebit * (1 - tax_rate)
        reinvestment = nopat * reinvestment_rate
        fcf = nopat - reinvestment
        discount_factor = 1 / ((1 + wacc) ** year)
        pv_fcf = fcf * discount_factor

        data.append([
            year, rev, ebit, nopat, reinvestment,
            fcf, discount_factor, pv_fcf
        ])

    df = pd.DataFrame(data, columns=[
        "Year", "Revenue", "EBIT", "NOPAT", "Reinvestment",
        "Free Cash Flow", "Discount Factor", "PV of FCF"
    ])

    final_fcf = df["Free Cash Flow"].iloc[-1]
    terminal_value = final_fcf * (1 + terminal_growth) / (wacc - terminal_growth)
    pv_terminal_value = terminal_value / ((1 + wacc) ** years)

    pv_projected_fcfs = df["PV of FCF"].sum()
    enterprise_value = pv_projected_fcfs + pv_terminal_value
    equity_value = enterprise_value - debt + cash
    intrinsic_value = equity_value / shares

    return df, terminal_value, pv_terminal_value, pv_projected_fcfs, enterprise_value, equity_value, intrinsic_value

df, terminal_value, pv_terminal_value, pv_projected_fcfs, enterprise_value, equity_value, intrinsic_value = run_dcf(
    revenue, growth, ebit_margin, tax_rate, reinvestment_rate,
    wacc, terminal_growth, years, debt, cash, shares
)

upside = (intrinsic_value / price - 1) if price > 0 else 0

if upside > 0.10:
    signal = "UNDERVALUED"
    color_class = "good"
elif upside < -0.10:
    signal = "OVERVALUED"
    color_class = "bad"
else:
    signal = "FAIRLY VALUED"
    color_class = "gold"

# ======================================================
# TOP DASHBOARD
# ======================================================
st.markdown(f"## {company_name} ({ticker})")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="card">
        <div>Intrinsic Value</div>
        <div class="{color_class}">${intrinsic_value:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.metric("Market Price", f"${price:,.2f}")

with col3:
    st.metric("Upside / Downside", f"{upside:.2%}", delta=f"{upside:.2%}")

with col4:
    st.markdown(f"""
    <div class="card">
        <div>Model Signal</div>
        <div class="{color_class}">{signal}</div>
    </div>
    """, unsafe_allow_html=True)

# ======================================================
# PROPER EXCEL DCF EXPORT
# ======================================================
def create_dcf_excel():
    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        blue = "#0C2340"
        gold = "#FFC72C"
        light_blue = "#D9EAF7"
        green = "#C6EFCE"
        red = "#FFC7CE"

        title_fmt = workbook.add_format({
            "bold": True,
            "font_size": 18,
            "font_color": blue
        })

        section_fmt = workbook.add_format({
            "bold": True,
            "bg_color": blue,
            "font_color": "white",
            "border": 1
        })

        header_fmt = workbook.add_format({
            "bold": True,
            "bg_color": gold,
            "font_color": blue,
            "border": 1,
            "align": "center"
        })

        input_fmt = workbook.add_format({
            "bg_color": light_blue,
            "border": 1
        })

        money_fmt = workbook.add_format({
            "num_format": "$#,##0.00",
            "border": 1
        })

        percent_fmt = workbook.add_format({
            "num_format": "0.00%",
            "border": 1
        })

        number_fmt = workbook.add_format({
            "num_format": "#,##0.00",
            "border": 1
        })

        formula_money_fmt = workbook.add_format({
            "bg_color": gold,
            "num_format": "$#,##0.00",
            "border": 1
        })

        formula_percent_fmt = workbook.add_format({
            "bg_color": gold,
            "num_format": "0.00%",
            "border": 1
        })

        explanation_fmt = workbook.add_format({
            "text_wrap": True,
            "border": 1,
            "valign": "top"
        })

        # ======================================================
        # ASSUMPTIONS SHEET
        # ======================================================
        ws_a = workbook.add_worksheet("Assumptions")

        ws_a.write("A1", "Future Worth DCF Model", title_fmt)
        ws_a.write("A3", "Input Assumptions", section_fmt)

        assumptions = [
            ("Ticker", ticker, input_fmt),
            ("Company Name", company_name, input_fmt),
            ("Current Revenue", revenue, money_fmt),
            ("Revenue Growth", growth, percent_fmt),
            ("EBIT Margin", ebit_margin, percent_fmt),
            ("Tax Rate", tax_rate, percent_fmt),
            ("Reinvestment Rate", reinvestment_rate, percent_fmt),
            ("WACC", wacc, percent_fmt),
            ("Terminal Growth", terminal_growth, percent_fmt),
            ("Projection Years", years, number_fmt),
            ("Debt", debt, money_fmt),
            ("Cash", cash, money_fmt),
            ("Shares Outstanding", shares, number_fmt),
            ("Current Market Price", price, money_fmt)
        ]

        for i, (label, value, fmt) in enumerate(assumptions, start=4):
            ws_a.write(i - 1, 0, label, header_fmt)
            ws_a.write(i - 1, 1, value, fmt)

        ws_a.set_column("A:A", 28)
        ws_a.set_column("B:B", 24)

        # ======================================================
        # DCF MODEL SHEET
        # ======================================================
        ws_dcf = workbook.add_worksheet("DCF Model")

        ws_dcf.write("A1", "Projected Free Cash Flow", title_fmt)
        ws_dcf.write("A3", "DCF Forecast", section_fmt)

        headers = [
            "Year",
            "Revenue",
            "EBIT",
            "NOPAT",
            "Reinvestment",
            "Free Cash Flow",
            "Discount Factor",
            "PV of FCF"
        ]

        for col, header in enumerate(headers):
            ws_dcf.write(3, col, header, header_fmt)

        for i in range(years):
            excel_row = 5 + i
            row_index = excel_row - 1

            ws_dcf.write(row_index, 0, i + 1, number_fmt)

            if i == 0:
                ws_dcf.write_formula(
                    row_index, 1,
                    "=Assumptions!$B$6*(1+Assumptions!$B$7)",
                    formula_money_fmt
                )
            else:
                ws_dcf.write_formula(
                    row_index, 1,
                    f"=B{excel_row-1}*(1+Assumptions!$B$7)",
                    formula_money_fmt
                )

            ws_dcf.write_formula(row_index, 2, f"=B{excel_row}*Assumptions!$B$8", formula_money_fmt)
            ws_dcf.write_formula(row_index, 3, f"=C{excel_row}*(1-Assumptions!$B$9)", formula_money_fmt)
            ws_dcf.write_formula(row_index, 4, f"=D{excel_row}*Assumptions!$B$10", formula_money_fmt)
            ws_dcf.write_formula(row_index, 5, f"=D{excel_row}-E{excel_row}", formula_money_fmt)
            ws_dcf.write_formula(row_index, 6, f"=1/(1+Assumptions!$B$11)^A{excel_row}", number_fmt)
            ws_dcf.write_formula(row_index, 7, f"=F{excel_row}*G{excel_row}", formula_money_fmt)

        last_row = 4 + years

        ws_dcf.set_column("A:A", 12)
        ws_dcf.set_column("B:F", 18)
        ws_dcf.set_column("G:G", 16)
        ws_dcf.set_column("H:H", 18)

        chart = workbook.add_chart({"type": "line"})
        chart.add_series({
            "name": "Free Cash Flow",
            "categories": f"='DCF Model'!$A$5:$A${last_row}",
            "values": f"='DCF Model'!$F$5:$F${last_row}",
            "line": {"color": blue, "width": 2.25}
        })

        chart.add_series({
            "name": "PV of FCF",
            "categories": f"='DCF Model'!$A$5:$A${last_row}",
            "values": f"='DCF Model'!$H$5:$H${last_row}",
            "line": {"color": gold, "width": 2.25}
        })

        chart.set_title({"name": "Projected Cash Flows"})
        chart.set_x_axis({"name": "Year"})
        chart.set_y_axis({"name": "Dollars"})
        ws_dcf.insert_chart("J4", chart)

        # ======================================================
        # VALUATION SUMMARY SHEET
        # ======================================================
        ws_s = workbook.add_worksheet("Valuation Summary")

        ws_s.write("A1", "Valuation Summary", title_fmt)
        ws_s.write("A3", "DCF Valuation Output", section_fmt)

        summary_rows = [
            ("PV of Projected FCF", f"=SUM('DCF Model'!H5:H{last_row})", formula_money_fmt),
            ("Terminal Value", f"='DCF Model'!F{last_row}*(1+Assumptions!$B$12)/(Assumptions!$B$11-Assumptions!$B$12)", formula_money_fmt),
            ("PV of Terminal Value", f"=B4/(1+Assumptions!$B$11)^Assumptions!$B$13", formula_money_fmt),
            ("Enterprise Value", "=B3+B5", formula_money_fmt),
            ("Less: Debt", "=Assumptions!$B$14", formula_money_fmt),
            ("Add: Cash", "=Assumptions!$B$15", formula_money_fmt),
            ("Equity Value", "=B6-B7+B8", formula_money_fmt),
            ("Shares Outstanding", "=Assumptions!$B$16", number_fmt),
            ("Intrinsic Value Per Share", "=B9/B10", formula_money_fmt),
            ("Current Market Price", "=Assumptions!$B$17", money_fmt),
            ("Upside / Downside", "=B11/B12-1", formula_percent_fmt)
        ]

        for i, (label, formula, fmt) in enumerate(summary_rows, start=3):
            ws_s.write(i - 1, 0, label, header_fmt)
            ws_s.write_formula(i - 1, 1, formula, fmt)

        ws_s.conditional_format("B13", {
            "type": "cell",
            "criteria": ">",
            "value": 0,
            "format": workbook.add_format({
                "bg_color": green,
                "font_color": "#006100",
                "num_format": "0.00%",
                "border": 1
            })
        })

        ws_s.conditional_format("B13", {
            "type": "cell",
            "criteria": "<",
            "value": 0,
            "format": workbook.add_format({
                "bg_color": red,
                "font_color": "#9C0006",
                "num_format": "0.00%",
                "border": 1
            })
        })

        ws_s.set_column("A:A", 28)
        ws_s.set_column("B:B", 24)

        # ======================================================
        # FORMULA EXPLANATION SHEET
        # ======================================================
        ws_e = workbook.add_worksheet("Formula Explanation")

        ws_e.write("A1", "How the DCF Model Works", title_fmt)

        explanation_headers = ["Line Item", "Formula", "Explanation"]

        for col, header in enumerate(explanation_headers):
            ws_e.write(2, col, header, header_fmt)

        explanations = [
            ("Revenue", "Prior Year Revenue × (1 + Revenue Growth)", "Projects company sales forward based on the selected growth assumption."),
            ("EBIT", "Revenue × EBIT Margin", "Estimates operating income before interest and taxes."),
            ("NOPAT", "EBIT × (1 - Tax Rate)", "Converts operating income into after-tax operating profit."),
            ("Reinvestment", "NOPAT × Reinvestment Rate", "Estimates how much profit must be reinvested to support growth."),
            ("Free Cash Flow", "NOPAT - Reinvestment", "Represents cash flow available to investors."),
            ("Discount Factor", "1 / (1 + WACC)^Year", "Discounts future cash flows back to present value."),
            ("PV of FCF", "Free Cash Flow × Discount Factor", "Calculates the present value of each year's projected cash flow."),
            ("Terminal Value", "Final Year FCF × (1 + Terminal Growth) / (WACC - Terminal Growth)", "Estimates the company's value after the forecast period."),
            ("Enterprise Value", "PV of Projected FCF + PV of Terminal Value", "Represents the total value of the operating business."),
            ("Equity Value", "Enterprise Value - Debt + Cash", "Converts enterprise value into value available to shareholders."),
            ("Intrinsic Value Per Share", "Equity Value / Shares Outstanding", "Calculates the estimated value of one share."),
            ("Upside / Downside", "Intrinsic Value Per Share / Current Market Price - 1", "Shows whether the DCF value is above or below the market price.")
        ]

        for i, row in enumerate(explanations, start=4):
            ws_e.write(i - 1, 0, row[0], header_fmt)
            ws_e.write(i - 1, 1, row[1], explanation_fmt)
            ws_e.write(i - 1, 2, row[2], explanation_fmt)

        ws_e.set_column("A:A", 24)
        ws_e.set_column("B:B", 48)
        ws_e.set_column("C:C", 70)

    output.seek(0)
    return output

# ======================================================
# TABS
# ======================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Executive Summary",
    "Price Chart",
    "DCF Build",
    "Bear/Base/Bull",
    "Peer Comps",
    "Excel Export",
    "Learn the Model"
])

with tab1:
    st.subheader("Executive Summary")

    st.write(f"""
    **Future Worth** estimates that **{company_name}** has an intrinsic value of 
    **${intrinsic_value:,.2f} per share**. The current market price is **${price:,.2f}**, 
    implying an estimated upside/downside of **{upside:.2%}**.
    """)

    if signal == "UNDERVALUED":
        st.success("🟢 Based on your assumptions, the stock appears undervalued.")
    elif signal == "OVERVALUED":
        st.error("🔴 Based on your assumptions, the stock appears overvalued.")
    else:
        st.info("🟡 Based on your assumptions, the stock appears fairly valued.")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Enterprise Value", format_dollar_large(enterprise_value))
    s2.metric("Equity Value", format_dollar_large(equity_value))
    s3.metric("Market Cap", format_dollar_large(market_cap))
    s4.metric("PV of Terminal Value", format_dollar_large(pv_terminal_value))

with tab2:
    st.subheader("Live Stock Price Chart")

    try:
        hist = stock.history(period="1y") if stock is not None else pd.DataFrame()

        if hist.empty:
            st.warning("No price history available.")
        else:
            price_chart = hist[["Close"]].copy()
            price_chart.index = pd.to_datetime(price_chart.index)
            st.line_chart(price_chart)

            start_price = price_chart["Close"].iloc[0]
            end_price = price_chart["Close"].iloc[-1]
            one_year_return = (end_price / start_price) - 1

            c1, c2, c3 = st.columns(3)
            c1.metric("1-Year Start Price", f"${start_price:,.2f}")
            c2.metric("Latest Close", f"${end_price:,.2f}")
            c3.metric("1-Year Return", f"{one_year_return:.2%}", delta=f"{one_year_return:.2%}")

    except Exception:
        st.warning("Could not load price chart.")

with tab3:
    st.subheader("DCF Projection Table")

    display_df = df.copy()

    for col in ["Revenue", "EBIT", "NOPAT", "Reinvestment", "Free Cash Flow", "PV of FCF"]:
        display_df[col] = display_df[col].apply(format_dollar_large)

    display_df["Discount Factor"] = display_df["Discount Factor"].map("{:.3f}".format)

    st.dataframe(display_df, use_container_width=True)

    st.subheader("Free Cash Flow vs Present Value")
    chart_df = df.copy()
    chart_df["Free Cash Flow"] = chart_df["Free Cash Flow"] / 1_000_000_000
    chart_df["PV of FCF"] = chart_df["PV of FCF"] / 1_000_000_000
    st.line_chart(chart_df.set_index("Year")[["Free Cash Flow", "PV of FCF"]])

with tab4:
    st.subheader("Bear / Base / Bull Scenario Analysis")

    scenarios = []
    scenario_inputs = [
        ("Bear Case", max(growth - 0.03, -0.10), wacc + 0.02, max(terminal_growth - 0.01, 0.0)),
        ("Base Case", growth, wacc, terminal_growth),
        ("Bull Case", growth + 0.03, max(wacc - 0.02, terminal_growth + 0.01), terminal_growth + 0.01)
    ]

    for name, s_growth, s_wacc, s_tg in scenario_inputs:
        result = run_dcf(
            revenue, s_growth, ebit_margin, tax_rate, reinvestment_rate,
            s_wacc, s_tg, years, debt, cash, shares
        )

        s_intrinsic = result[-1]
        s_upside = (s_intrinsic / price - 1) if price > 0 else 0

        scenarios.append([
            name, s_growth, s_wacc, s_tg,
            s_intrinsic, s_upside, price
        ])

    scenario_df = pd.DataFrame(scenarios, columns=[
        "Scenario", "Revenue Growth", "WACC", "Terminal Growth",
        "Intrinsic Value", "Upside / Downside", "Current Market Price"
    ])

    display_scenarios = scenario_df.copy()
    display_scenarios["Revenue Growth"] = display_scenarios["Revenue Growth"].map("{:.2%}".format)
    display_scenarios["WACC"] = display_scenarios["WACC"].map("{:.2%}".format)
    display_scenarios["Terminal Growth"] = display_scenarios["Terminal Growth"].map("{:.2%}".format)
    display_scenarios["Intrinsic Value"] = display_scenarios["Intrinsic Value"].map("${:,.2f}".format)
    display_scenarios["Upside / Downside"] = display_scenarios["Upside / Downside"].map("{:.2%}".format)
    display_scenarios["Current Market Price"] = display_scenarios["Current Market Price"].map("${:,.2f}".format)

    st.dataframe(display_scenarios, use_container_width=True)

    base_chart = alt.Chart(scenario_df).mark_bar(color="#FFC72C").encode(
        x=alt.X("Scenario:N", title="Scenario"),
        y=alt.Y("Intrinsic Value:Q", title="Intrinsic Value Per Share"),
        tooltip=["Scenario", "Intrinsic Value", "Current Market Price"]
    )

    market_line = alt.Chart(pd.DataFrame({"Current Market Price": [price]})).mark_rule(
        color="#FFFFFF",
        strokeDash=[6, 4],
        size=3
    ).encode(y="Current Market Price:Q")

    st.altair_chart((base_chart + market_line).properties(height=400), use_container_width=True)
    st.caption("White dashed line = current market price.")

with tab5:
    st.subheader("Comparable Company Snapshot")

    peers_input = st.text_input(
        "Enter peer tickers separated by commas",
        value="MSFT,GOOGL,AMZN"
    )

    peer_tickers = [x.strip().upper() for x in peers_input.split(",") if x.strip()]
    comps = []

    try:
        selected_ev = info.get("enterpriseValue", np.nan)
        selected_revenue = info.get("totalRevenue", np.nan)
        selected_ebitda = info.get("ebitda", np.nan)
        selected_ev_sales = selected_ev / selected_revenue if selected_revenue and selected_revenue > 0 else np.nan
        selected_ev_ebitda = selected_ev / selected_ebitda if selected_ebitda and selected_ebitda > 0 else np.nan

        comps.append([
            ticker, company_name, price, market_cap, revenue,
            selected_ev_sales, selected_ev_ebitda, "Target"
        ])
    except Exception:
        pass

    for peer in peer_tickers:
        try:
            peer_stock = yf.Ticker(peer)
            peer_info = peer_stock.info

            peer_name = peer_info.get("shortName", peer)
            peer_price = peer_info.get("currentPrice", np.nan)
            peer_market_cap = peer_info.get("marketCap", np.nan)
            peer_revenue = peer_info.get("totalRevenue", np.nan)
            peer_ev = peer_info.get("enterpriseValue", np.nan)
            peer_ebitda = peer_info.get("ebitda", np.nan)

            ev_sales = peer_ev / peer_revenue if peer_revenue and peer_revenue > 0 else np.nan
            ev_ebitda = peer_ev / peer_ebitda if peer_ebitda and peer_ebitda > 0 else np.nan

            comps.append([
                peer, peer_name, peer_price, peer_market_cap, peer_revenue,
                ev_sales, ev_ebitda, "Peer"
            ])

        except Exception:
            pass

    comps_df = pd.DataFrame(comps, columns=[
        "Ticker", "Company", "Price", "Market Cap", "Revenue",
        "EV/Sales", "EV/EBITDA", "Type"
    ])

    if comps_df.empty:
        st.warning("No peer data loaded.")
    else:
        display_comps = comps_df.copy()
        display_comps["Price"] = display_comps["Price"].map("${:,.2f}".format)
        display_comps["Market Cap"] = display_comps["Market Cap"].apply(format_dollar_large)
        display_comps["Revenue"] = display_comps["Revenue"].apply(format_dollar_large)
        display_comps["EV/Sales"] = display_comps["EV/Sales"].map("{:.2f}x".format)
        display_comps["EV/EBITDA"] = display_comps["EV/EBITDA"].map("{:.2f}x".format)

        st.dataframe(display_comps, use_container_width=True)

        target_ev_sales = comps_df.loc[comps_df["Ticker"] == ticker, "EV/Sales"].iloc[0]

        peer_chart = alt.Chart(comps_df).mark_bar(color="#FFC72C").encode(
            x=alt.X("Ticker:N", title="Ticker"),
            y=alt.Y("EV/Sales:Q", title="EV/Sales Multiple"),
            tooltip=["Ticker", "Company", "EV/Sales", "Type"]
        )

        target_line = alt.Chart(pd.DataFrame({"Target EV/Sales": [target_ev_sales]})).mark_rule(
            color="#FFFFFF",
            strokeDash=[6, 4],
            size=3
        ).encode(y="Target EV/Sales:Q")

        st.subheader("Peer EV/Sales Comparison")
        st.altair_chart((peer_chart + target_line).properties(height=400), use_container_width=True)
        st.caption(f"White dashed line = {ticker}'s current EV/Sales multiple.")

with tab6:
    st.subheader("Download Formula-Based Excel DCF")

    st.write("""
    This Excel file matches the app’s output, includes formula-coded cells,
    properly discounts projected cash flows, calculates terminal value,
    and clearly shows how the intrinsic value per share is calculated.
    """)

    excel_file = create_dcf_excel()

    st.download_button(
        label="Download Excel DCF Model",
        data=excel_file,
        file_name=f"{ticker}_Future_Worth_DCF.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with tab7:
    st.subheader("How Future Worth Calculates Value")

    with st.expander("1. Revenue Forecast"):
        st.write("Revenue is projected forward using the selected revenue growth rate.")

    with st.expander("2. EBIT"):
        st.write("EBIT is calculated by multiplying revenue by EBIT margin.")

    with st.expander("3. NOPAT"):
        st.write("NOPAT is operating profit after taxes.")

    with st.expander("4. Free Cash Flow"):
        st.write("Free cash flow equals NOPAT minus reinvestment.")

    with st.expander("5. Discounting"):
        st.write("Future free cash flows are discounted back to today using WACC.")

    with st.expander("6. Terminal Value"):
        st.write("Terminal value estimates the value of the company after the projection period.")

    with st.expander("7. Equity Value"):
        st.write("Enterprise value minus debt plus cash equals equity value. Equity value divided by shares gives intrinsic value per share.")

    assumptions_df = pd.DataFrame({
        "Assumption": [
            "Revenue Growth", "WACC", "Terminal Growth",
            "EBIT Margin", "Tax Rate", "Reinvestment Rate"
        ],
        "Value Used": [
            f"{growth:.2%}", f"{wacc:.2%}", f"{terminal_growth:.2%}",
            f"{ebit_margin:.2%}", f"{tax_rate:.2%}", f"{reinvestment_rate:.2%}"
        ],
        "Purpose": [
            "Projects sales growth",
            "Discounts future cash flows",
            "Estimates long-term growth",
            "Estimates operating profitability",
            "Calculates after-tax operating profit",
            "Estimates required reinvestment"
        ]
    })

    st.dataframe(assumptions_df, use_container_width=True)