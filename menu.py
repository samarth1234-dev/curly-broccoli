import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

# -----------------------
# Streamlit Financial Menu
# -----------------------
# Single-file app that provides a clean menu-driven interface for a
# financial management front-end where users can insert/manage links,
# add transactions, view simple charts, and export data.

st.set_page_config(page_title="Finance Hub", page_icon="💼", layout="wide")

# ---- Styles ----
st.markdown(
    """
    <style>
    /* page background */
    .stApp { background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 100%); }
    /* card */
    .card { padding: 1rem; border-radius: 12px; box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06); background: white; }
    .muted { color: #6b7280; }
    .link-card { padding: .6rem .8rem; border-radius: 10px; border: 1px solid #eef2f7; margin-bottom: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_DIR = "./.streamlit_data"
LINKS_FILE = os.path.join(DATA_DIR, "links.json")
TRANS_FILE = os.path.join(DATA_DIR, "transactions.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

# ---- Utilities ----

def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# Initialize session state
if "links" not in st.session_state:
    st.session_state.links = load_json(LINKS_FILE, [])

if "transactions" not in st.session_state:
    st.session_state.transactions = load_json(TRANS_FILE, [])


# ---- Sidebar menu ----
st.sidebar.title("Finance Hub")
menu = st.sidebar.radio("Navigate", ["Dashboard", "Transactions", "Budgets", "Investments", "Links", "Reports", "Settings"]) 

st.sidebar.markdown("---")
if st.sidebar.button("Save data to disk"):
    save_json(LINKS_FILE, st.session_state.links)
    save_json(TRANS_FILE, st.session_state.transactions)
    st.sidebar.success("Saved ✅")

st.sidebar.caption("Built with Streamlit — customize freely")

# ---- Page implementations ----

# --- Dashboard ---
if menu == "Dashboard":
    st.title("Finance Hub — Dashboard")
    col1, col2, col3 = st.columns([1, 2, 1])

    # simple KPIs
    total_balance = sum([t["amount"] for t in st.session_state.transactions]) if st.session_state.transactions else 0
    income = sum([t["amount"] for t in st.session_state.transactions if t["type"] == "Income"]) if st.session_state.transactions else 0
    expense = sum([t["amount"] for t in st.session_state.transactions if t["type"] == "Expense"]) if st.session_state.transactions else 0

    col1.metric("Total balance", f"₹{total_balance:,.2f}")
    col2.metric("Income (total)", f"₹{income:,.2f}")
    col3.metric("Expense (total)", f"₹{expense:,.2f}")

    st.markdown("---")

    # Recent transactions table
    st.subheader("Recent transactions")
    if st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        st.dataframe(df.sort_values(by="date", ascending=False).head(10).reset_index(drop=True))
    else:
        st.info("No transactions yet. Add some under the Transactions tab.")

    st.markdown("---")

    # Simple chart
    st.subheader("Monthly snapshot (sample)")
    if st.session_state.transactions:
        dfc = pd.DataFrame(st.session_state.transactions)
        dfc["date"] = pd.to_datetime(dfc["date"]).dt.to_period("M").dt.to_timestamp()
        summary = dfc.groupby(["date", "type"]).amount.sum().reset_index()
        fig = px.bar(summary, x="date", y="amount", color="type", barmode="group", title="Income vs Expense by Month")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Month charts will appear here after you add transactions.")


# --- Transactions ---
elif menu == "Transactions":
    st.title("Transactions")

    with st.form("add_txn", clear_on_submit=True):
        st.subheader("Add a transaction")
        col1, col2, col3 = st.columns(3)
        with col1:
            ttype = st.selectbox("Type", ["Expense", "Income"])
            amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
        with col2:
            category = st.text_input("Category", value=("Salary" if ttype == "Income" else "General"))
            date = st.date_input("Date", value=datetime.today())
        with col3:
            notes = st.text_input("Notes (optional)")

        submitted = st.form_submit_button("Add transaction")
        if submitted:
            txn = {"type": ttype, "amount": float(amount), "category": category, "date": date.isoformat(), "notes": notes}
            st.session_state.transactions.append(txn)
            save_json(TRANS_FILE, st.session_state.transactions)
            st.success("Transaction added")

    st.markdown("---")
    st.subheader("All transactions")
    if st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        st.dataframe(df.sort_values(by="date", ascending=False).reset_index(drop=True))
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="transactions.csv", mime="text/csv")
    else:
        st.info("No transactions yet — use the form above to add some.")


# --- Budgets ---
elif menu == "Budgets":
    st.title("Budgets")
    st.info("Simple, local budget placeholders — extend this with persistence or connect to your db.")
    categories = ["Food", "Rent", "Utilities", "Transport", "Entertainment"]
    bud = {c: st.number_input(f"Budget for {c} (₹)", min_value=0.0, value=0.0) for c in categories}
    if st.button("Save budgets (session-only)"):
        st.session_state.budgets = bud
        st.success("Saved to session state")

    if "budgets" in st.session_state:
        st.write(st.session_state.budgets)


# --- Investments ---
elif menu == "Investments":
    st.title("Investments")
    st.write("Track assets or paste a small portfolio below (CSV style: name,quantity,price)")
    portfolio_text = st.text_area("Paste portfolio (CSV) or leave empty for sample", value="")
    if st.button("Parse portfolio"):
        if portfolio_text.strip():
            lines = [l.strip() for l in portfolio_text.splitlines() if l.strip()]
            rows = []
            for l in lines:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 3:
                    name, qty, price = parts[:3]
                    try:
                        rows.append({"name": name, "qty": float(qty), "price": float(price)})
                    except:
                        st.warning(f"Skipping invalid row: {l}")
            if rows:
                df = pd.DataFrame(rows)
                df["value"] = df.qty * df.price
                st.dataframe(df)
                st.metric("Portfolio value", f"₹{df['value'].sum():,.2f}")
            else:
                st.info("No valid rows parsed.")
        else:
            st.info("Paste CSV lines to parse.")


# --- Links management ---
elif menu == "Links":
    st.title("Links — quick access & management")
    st.write("Use this page to store and organise your finance-related links (banking, bills, docs, dashboards).")

    with st.form("add_link", clear_on_submit=True):
        name = st.text_input("Link name", value="e.g. My bank")
        url = st.text_input("URL (include https://)")
        tag = st.selectbox("Tag", ["Bank", "Bills", "Docs", "Broker", "Other"]) 
        add = st.form_submit_button("Add link")
        if add:
            if name and url:
                entry = {"name": name, "url": url, "tag": tag, "created": datetime.now().isoformat()}
                st.session_state.links.append(entry)
                save_json(LINKS_FILE, st.session_state.links)
                st.success("Link added ✅")
            else:
                st.error("Please provide both a name and a URL.")

    st.markdown("---")
    st.subheader("Saved links")
    if st.session_state.links:
        # filter
        tags = [l.get("tag", "Other") for l in st.session_state.links]
        uniq = ["All"] + sorted(list(set(tags)))
        sel = st.selectbox("Filter by tag", uniq)

        for i, l in enumerate(st.session_state.links):
            if sel != "All" and l.get("tag") != sel:
                continue
            st.markdown(
                f"<div class='link-card'><strong>{l['name']}</strong> <span class='muted'>({l.get('tag','')})</span><br/><a href='{l['url']}' target='_blank'>{l['url']}</a></div>",
                unsafe_allow_html=True,
            )

        if st.button("Export links as JSON"):
            st.download_button("Download links.json", data=json.dumps(st.session_state.links, indent=2), file_name="links.json")
    else:
        st.info("No links yet — add one using the form above.")


# --- Reports ---
elif menu == "Reports":
    st.title("Reports")
    st.write("Quick charts & simple exportable reports")

    if st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        by_cat = df.groupby(["category", "type"]).amount.sum().reset_index()
        st.subheader("Spending / Income by category")
        fig = px.sunburst(by_cat, path=["type", "category"], values="amount")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Export reports")
        st.download_button("Download transactions JSON", data=json.dumps(st.session_state.transactions, indent=2), file_name="transactions.json")
    else:
        st.info("No transactions to report on yet.")


# --- Settings ---
elif menu == "Settings":
    st.title("Settings")
    st.write("App-level options")

    if st.button("Clear all data (links + transactions)"):
        st.session_state.links = []
        st.session_state.transactions = []
        try:
            if os.path.exists(LINKS_FILE):
                os.remove(LINKS_FILE)
            if os.path.exists(TRANS_FILE):
                os.remove(TRANS_FILE)
        except Exception:
            pass
        st.success("Data cleared from session and disk.")

    st.markdown("---")
    st.subheader("Theme & appearance")
    cols = st.columns(3)
    with cols[0]:
        if st.button("Apply compact look"):
            st.experimental_set_query_params(theme="compact")
            st.success("Applied (simulated) — you can add your own CSS")
    with cols[1]:
        st.write("Streaming tip:")
        st.caption("Right now this app saves to a local folder .streamlit_data — for multi-user use, connect to a DB.")

    st.markdown("---")
    st.caption("Made with ❤ — customise icons, colors, and persistence as you like.")

# ---- Footer ----
st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown("<div class='muted'>Finance Hub — example Streamlit app · customize for your workflows · export data for backups</div>", unsafe_allow_html=True)
