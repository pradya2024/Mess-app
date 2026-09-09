import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import requests
import json

# Page Configuration
st.set_page_config(page_title="ANNAPURNA VEGETABLE SHOP", page_icon="🥦", layout="centered")

# --- CUSTOM CSS FOR SHOP BRANDING ---
st.markdown("""
<style>
    .stApp, p, label, .stMarkdown, .stSelectbox, div[data-baseweb="select"] { color: #222222 !important; }
    .shop-header {
        background: linear-gradient(135deg, #FF9800, #F57C00);
        color: white !important; padding: 20px; border-radius: 12px;
        text-align: center; margin-bottom: 20px;
    }
    .shop-header h1 { color: white !important; font-size: 24px !important; margin: 0; }
</style>
""", unsafe_allow_html=True)

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxbbUBdxj__qToZfF33nT2E3E464K9i3v6S9vDSaxLx4ll8nwNrY8gDaDQqN2sfJbQ2/exec"

st.markdown('<div class="shop-header"><h1>🚩 ANNAPURNA VEGETABLE SHOP</h1><p>Mess Supply System</p></div>', unsafe_allow_html=True)

USER_CREDENTIALS = {
    "admin": "admin123", "hq": "hq123", "rtt": "rtt123", "ffc": "ffc123", 
    "fc": "fc123", "so_s": "so123", "go_s": "go123", "veg_shop": "veg123"
}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'mandi_rates' not in st.session_state: st.session_state.mandi_rates = {}

def get_ist_now():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

try:
    response = requests.get(SCRIPT_URL, timeout=5)
    api_data = response.json()
    available_items = api_data.get("items", ["Aloo", "Tamatar", "Pyaj"])
    raw_demands = api_data.get("demands", [])
    df = pd.DataFrame(raw_demands) if raw_demands else pd.DataFrame(columns=["Date", "Mess", "Item", "Qty", "Rate", "Total"])
except Exception:
    available_items = ["Aloo", "Tamatar", "Pyaj"]
    df = pd.DataFrame(columns=["Date", "Mess", "Item", "Qty", "Rate", "Total"])

for item in available_items:
    if item not in st.session_state.mandi_rates: st.session_state.mandi_rates[item] = 0.0

if not st.session_state.logged_in:
    st.subheader("🔒 Login Karein")
    user_input = st.text_input("Username:").strip().lower()
    pass_input = st.text_input("Password:", type="password")
    if st.button("Login ✅"):
        if user_input in USER_CREDENTIALS and USER_CREDENTIALS[user_input] == pass_input:
            st.session_state.logged_in = True
            st.session_state.username = user_input
            st.rerun()
        else: st.error("❌ Galat Username ya Password!")
else:
    name_mapping = {"hq": "HQ", "rtt": "RTT", "ffc": "FFC", "fc": "FC", "so_s": "SO'S", "go_s": "GO'S", "veg_shop": "VEG SHOP"}
    display_name = name_mapping.get(st.session_state.username, "ADMIN")
    st.sidebar.write(f"👤 User: **{display_name}**")
    if st.sidebar.button("Logout 🚪"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # ---- 🟢 MESS MANAGER SCREEN ----
    if st.session_state.username != "admin":
        st.subheader("📋 New Demand Form")
        current_mess = name_mapping[st.session_state.username]
        with st.form("demand_form", clear_on_submit=True):
            item = st.selectbox("Select Item:", available_items)
            qty = st.number_input("Quantity:", min_value=1.0, step=1.0)
            unit = st.selectbox("Select Unit (इकाई):", ["Kg", "Dozen", "Pcs", "Bundle"])
            if st.form_submit_button("Submit Demand 🚀"):
                current_ist_date = get_ist_now().strftime("%Y-%m-%d")
                item_with_unit = f"{item} ({unit})"
                payload = {"action": "submit_demand", "Date": current_ist_date, "Mess": current_mess, "Item": item_with_unit, "Qty": qty, "Rate": 0, "Total": 0}
                try:
                    res = requests.post(SCRIPT_URL, data=json.dumps(payload))
                    if res.status_code == 200:
                        st.success("✅ Demand Record Ho Gayi!")
                        st.balloons()
                    else: st.error("⚠️ Server Error!")
                except Exception: st.error("❌ Connection Error!")
                    
    # ---- 📊 ADMIN SCREEN ----
    else:
        today_ist = get_ist_now().date()
        selected_date = st.date_input("Select Date:", value=today_ist)
        formatted_date = selected_date.strftime("%Y-%m-%d")
        
        if not df.empty and "Date" in df.columns:
            def to_clean_date(val):
                try: return pd.to_datetime(str(val).strip()).date() + timedelta(days=1)
                except Exception:
                    try: return datetime.strptime(str(val).strip()[:10], "%Y-%m-%d").date() + timedelta(days=1)
                    except Exception: return None
            df["Parsed_Date"] = df["Date"].apply(to_clean_date)
            filtered_df = df[df["Parsed_Date"] == selected_date].reset_index(drop=True)
            df["Month_Year"] = df["Date"].astype(str).str.slice(0, 7)
        else: filtered_df = df.copy()

        tab1, tab2, tab3, tab4 = st.tabs(["🛒 Packing List", "➕ Add Sabji", "💰 Mandi Rates & Qty", "💵 Mess Bills & Print"])
        
        # TAB 1: Packing List Matrix (Sl No 1 se start)
        with tab1:
            st.subheader("🛒 Mandi Purchase List")
            if filtered_df.empty: st.info("No demands found for this date.")
            else:
                filtered_df["Qty"] = pd.to_numeric(filtered_df["Qty"], errors='coerce').fillna(0)
                try:
                    matrix_df = filtered_df.pivot_table(index='Item', columns='Mess', values='Qty', aggfunc='sum', fill_value=0)
                    matrix_df['Total Qty'] = matrix_df.sum(axis=1)
                    matrix_df = matrix_df.reset_index()
                    matrix_df.index = matrix_df.index + 1
                    matrix_df.index.name = "Sl No"
                    st.dataframe(matrix_df.reset_index())
                except Exception: st.dataframe(filtered_df[["Date", "Mess", "Item", "Qty"]])

        # TAB 2: Nayi Sabji Add
        with tab2:
            st.subheader("➕ Nayi Sabji Jodein")
            with st.form("add_item_form", clear_on_submit=True):
                new_item = st.text_input("Item Name:").strip()
                if st.form_submit_button("Add Item ➕") and new_item:
                    try:
                        res = requests.post(SCRIPT_URL, data=json.dumps({"action": "add_item", "item_name": new_item}))
                        if res.status_code == 200: st.success("✅ Jodh diya gaya!"); st.rerun()
                        else: st.error("⚠️ Error!")
                    except Exception: st.error("❌ Error!")

        # TAB 3: Rates & Quantity Edit Tab
        with tab3:
            st.subheader("💰 Aaj Ke Rates Aur Quantity Set Karein")
            st.info("Aap yahan se kisi bhi item ka Rate aur ordered Quantity dono badal sakte hain.")
            with st.form("rates_qty_form"):
                updated_rates = {}
                updated_qtys = {}
                for item in available_items:
                    val = st.session_state.mandi_rates.get(item, 0.0)
                    col1, col2 = st.columns(2)
                    with col1:
                        updated_rates[item] = st.number_input(f"Rate for {item}:", min_value=0.0, value=float(val), step=1.0, key=f"r_{item}")
                    with col2:
                        current_qty = 0.0
                        if not filtered_df.empty and item in filtered_df["Item"].values:
                            current_qty = float(filtered_df[filtered_df["Item"] == item]["Qty"].sum())
                        updated_qtys[item] = st.number_input(f"Qty for {item}:", min_value=0.0, value=current_qty, step=1.0, key=f"q_{item}")
                
                if st.form_submit_button("Save Rates & Quantity 💾"):
                    for item, r_val in updated_rates.items(): st.session_state.mandi_rates[item] = r_val
                    payload = {"action": "update_rates_and_qty", "Date": formatted_date, "rates": updated_rates, "qtys": updated_qtys}
                    try:
                        res = requests.post(SCRIPT_URL, data=json.dumps(payload))
                        st.success("✅ Rates and Quantity Updated successfully!") if res.status_code == 200 else st.warning("⚠️ Local save hua.")
                    except Exception: st.error("❌ Error!")

        # TAB 4: Bills, Monthly Summary & Custom Branded CSV Download
        with tab4:
            st.subheader("💵 All Mess Bills & Invoices")
            
            # 📊 Monthly Filter Option
            view_mode = st.radio("View Mode:", ["Daily Bill", "Monthly Summary"])
            
            working_df = filtered_df.copy()
            if view_mode == "Monthly Summary" and not df.empty:
                current_month = formatted_date[:7]
                working_df = df[df["Month_Year"] == current_month].reset_index(drop=True)
            
            if working_df.empty: st.info("No bills available for selected period.")
            else:
                working_df["Qty"] = pd.to_numeric(working_df["Qty"], errors='coerce').fillna(0)
                working_df["Rate"] = working_df["Item"].map(st.session_state.mandi_rates).fillna(0.0)
                working_df["Total"] = working_df["Qty"] * working_df["Rate"]
                
                st.write("### 📋 Total Bill Summary")
                sum_df = working_df.groupby("Mess")["Total"].sum().reset_index()
                sum_df.index = sum_df.index + 1
                sum_df.index.name = "Sl No"
                st.dataframe(sum_df.reset_index(), use_container_width=True)
                
                st.markdown("---")
                st.write("### 🔍 Detailed Bill & Print Invoice")
                sel_mess = st.selectbox("Select Mess For Bill Download/Print:", list(name_mapping.values()))
                
