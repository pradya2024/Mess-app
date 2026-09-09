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

# भारतीय समय (IST) निकालने का सही तरीका
def get_ist_now():
    utc_now = datetime.utcnow()
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return ist_now

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
        else:
            st.error("❌ Galat Username ya Password!")
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
            if st.form_submit_button("Submit Demand 🚀"):
                # भारत के करंट दिन की तारीख भेजना
                current_ist_date = get_ist_now().strftime("%Y-%m-%d")
                payload = {"action": "submit_demand", "Date": current_ist_date, "Mess": current_mess, "Item": item, "Qty": qty, "Rate": 0, "Total": 0}
                try:
                    res = requests.post(SCRIPT_URL, data=json.dumps(payload))
                    if res.status_code == 200:
                        st.success("✅ Demand Record Ho Gayi!")
                        st.balloons()
                    else:
                        st.error("⚠️ Server Error! Status Code: " + str(res.status_code))
                except Exception:
                    st.error("❌ Connection Error!")
                    
    # ---- 📊 ADMIN SCREEN ----
    else:
        today_ist = get_ist_now().date()
        selected_date = st.date_input("Select Date:", value=today_ist)
        
        # 🚩 फ़िक्स लॉजिक: शीट की तारीख अगर पीछे है, तो उसे +1 दिन आगे शिफ्ट करके देखना
        if not df.empty and "Date" in df.columns:
            def to_clean_date(val):
                try:
                    parsed_date = pd.to_datetime(str(val).strip()).date()
                    # अगर डेटाबेस में पुरानी तारीख (कल की) दिखा रहा है, तो टाइमज़ोन सुधार के लिए 1 दिन जोड़ें
                    return parsed_date + timedelta(days=1)
                except Exception:
                    try:
                        parsed_date = datetime.strptime(str(val).strip()[:10], "%Y-%m-%d").date()
                        return parsed_date + timedelta(days=1)
                    except Exception:
                        return None

            df["Parsed_Date"] = df["Date"].apply(to_clean_date)
            filtered_df = df[df["Parsed_Date"] == selected_date].reset_index(drop=True)
        else:
            filtered_df = df.copy()

        tab1, tab2, tab3, tab4 = st.tabs(["🛒 Packing List", "➕ Add Sabji", "💰 Mandi Rates", "💵 Mess Bills"])
        
        with tab1:
            st.subheader("🛒 Mandi Purchase List")
            if filtered_df.empty:
                st.info("No demands found for this date. (Try changing the date to check older items)")
            else:
                filtered_df["Qty"] = pd.to_numeric(filtered_df["Qty"], errors='coerce').fillna(0)
                try:
                    matrix_df = filtered_df.pivot_table(index='Item', columns='Mess', values='Qty', aggfunc='sum', fill_value=0)
                    matrix_df['Total Qty'] = matrix_df.sum(axis=1)
                    st.dataframe(matrix_df.reset_index())
                except Exception:
                    st.dataframe(filtered_df[["Date", "Mess", "Item", "Qty"]])

        with tab2:
            st.subheader("➕ Nayi Sabji Jodein")
            with st.form("add_item_form", clear_on_submit=True):
                new_item = st.text_input("Item Name:").strip()
                if st.form_submit_button("Add Item ➕") and new_item:
                    try:
                        res = requests.post(SCRIPT_URL, data=json.dumps({"action": "add_item", "item_name": new_item}))
                        if res.status_code == 200:
                            st.success("✅ Jodh diya gaya!")
                            st.rerun()
                        else:
                            st.error("⚠️ Error!")
                    except Exception:
                        st.error("❌ Error!")

        with tab3:
            st.subheader("💰 Aaj Ke Rates Set Karein")
            with st.form("rates_form"):
                updated_rates = {}
                for item in available_items:
                    val = st.session_state.mandi_rates.get(item, 0.0)
                    updated_rates[item] = st.number_input(f"Rate for {item}:", min_value=0.0, value=float(val), step=1.0, key=f"r_{item}")
                if st.form_submit_button("Save Rates 💾"):
                    for item, r_val in updated_rates.items(): st.session_state.mandi_rates[item] = r_val
                    try:
                        res = requests.post(SCRIPT_URL, data=json.dumps({"action": "update_rates", "Date": selected_date.strftime("%Y-%m-%d"), "rates": updated_rates}))
                        if res.status_code == 200:
                            st.success("✅ Rates Saved!")
                        else:
                            st.warning("⚠️ Local save hua.")
                    except Exception:
                        st.error("❌ Error!")

        with tab4:
            st.subheader("💵 All Mess Bills")
            if filtered_df.empty:
                st.info("No bills available.")
            else:
                filtered_df["Qty"] = pd.to_numeric(filtered_df["Qty"], errors='coerce').fillna(0)
                filtered_df["Rate"] = filtered_df["Item"].map(st.session_state.mandi_rates).fillna(0.0)
                filtered_df["Total"] = filtered_df["Qty"] * filtered_df["Rate"]
                
                st.write("### Summary")
                st.dataframe(filtered_df.groupby("Mess")["Total"].sum().reset_index())
                st.write("### Details")
                sel_mess = st.selectbox("Select Mess:", list(name_mapping.values()))
                m_det = filtered_df[filtered_df["Mess"] == sel_mess][["Item", "Qty", "Rate", "Total"]].reset_index(drop=True)
                st.dataframe(m_det)
                st.metric(label="Total Bill", value=f"₹{m_det['Total'].sum():,.2f}")
