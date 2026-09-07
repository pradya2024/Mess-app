import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# Page Configuration
st.set_page_config(page_title="Mess Supply Pro", page_icon="🥦", layout="centered")

# 🟢 APNI GOOGLE WEB APP KI LAMBI LINK YAHAN DAALEIN
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxbbUBdxj__qToZfF33nT2E3E464K9i3v6S9vDSaxLx4ll8nwNrY8gDaDQqN2sfJbQ2/exec"

st.title("📱 Mess Supply Pro")
st.write("Master Demand & Mandi Billing System")

# --- LOGIN CREDENTIALS ---
USER_CREDENTIALS = {
    "admin": "admin123",
    "hq": "hq123", "rtt": "rtt123", "ffc": "ffc123", 
    "fc": "fc123", "so_s": "so123", "go_s": "go123", "veg_shop": "veg123"
}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'mandi_rates' not in st.session_state: st.session_state.mandi_rates = {}

# Google Script API se live database load karna (Demands aur Sabji List dono)
try:
    response = requests.get(SCRIPT_URL)
    api_data = response.json()
    available_items = api_data.get("items", ["Aloo", "Tamatar", "Pyaj"])
    raw_demands = api_data.get("demands", [])
    if raw_demands:
        df = pd.DataFrame(raw_demands)
    else:
        df = pd.DataFrame(columns=["Date", "Mess", "Item", "Qty", "Rate", "Total"])
except:
    available_items = ["Aloo", "Tamatar", "Pyaj"]
    df = pd.DataFrame(columns=["Date", "Mess", "Item", "Qty", "Rate", "Total"])

# Session rates ko sync karna
for item in available_items:
    if item not in st.session_state.mandi_rates:
        st.session_state.mandi_rates[item] = 0.0

# ==========================================
# 🔐 SCREEN 1: LOGIN SYSTEM
# ==========================================
if not st.session_state.logged_in:
    st.subheader("🔒 Login Karein")
    user_input = st.text_input("Username:").strip().lower()
    pass_input = st.text_input("Password:", type="password")
    login_btn = st.button("Login ✅")
    
    if login_btn:
        if user_input in USER_CREDENTIALS and USER_CREDENTIALS[user_input] == pass_input:
            st.session_state.logged_in = True
            st.session_state.username = user_input
            st.rerun()
        else:
            st.error("❌ Galat Username ya Password!")

# ==========================================
# 🔓 SCREEN 2: MAIN APP
# ==========================================
else:
    name_mapping = {
        "hq": "HQ", "rtt": "RTT", "ffc": "FFC", "fc": "FC", 
        "so_s": "SO'S", "go_s": "GO'S", "veg_shop": "VEG SHOP"
    }
    
    display_name = name_mapping.get(st.session_state.username, "ADMIN")
    st.sidebar.write(f"👤 Logged in as: **{display_name}**")
    
    if st.sidebar.button("Logout 🚪"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # ---- 🟢 MESS MANAGER LOGGED IN ----
    if st.session_state.username != "admin":
        st.subheader("📋 New Demand Form")
        current_mess = name_mapping[st.session_state.username]
        st.info(f"Aap {current_mess} ke liye demand daal rahe hain.")
        
        with st.form("demand_form", clear_on_submit=True):
            item = st.selectbox("Select Sabji / Fruit Name:", available_items)
            qty = st.number_input("Quantity (Kg / Dozen):", min_value=1.0, step=1.0)
            submit = st.form_submit_button("Submit Demand 🚀")
            
            if submit:
                payload = {
                    "action": "submit_demand",
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Mess": current_mess,
                    "Item": item,
                    "Qty": qty,
                    "Rate": 0,
                    "Total": 0
                }
                try:
                    res = requests.post(SCRIPT_URL, data=json.dumps(payload))
                    if res.status_code == 200:
                        st.success(f"✅ Success: {item} ki {qty} Qty demand record ho gayi!")
                        st.balloons()
                    else:
                        st.error("⚠️ Error!")
                except:
                    st.error("❌ Connection Error.")
                
    # ---- 📊 ADMIN (OWNER) LOGGED IN ----
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["🛒 Mandi Packing List", "➕ Add New Sabji/Fruit", "💰 Today's Mandi Rates", "💵 Final Mess Bills"])
        
        # TAB 1: Packing List
        with tab1:
            st.subheader("🛒 Mandi Purchase Consolidated List")
            if df.empty or len(df) == 0:
                st.info("Abhi tak kisi bhi mess ne demand nahi bheji hai.")
            else:
                df["Qty"] = pd.to_numeric(df["Qty"], errors='coerce').fillna(0)
                mandi_list = df.groupby("Item")["Qty"].sum().reset_index()
                st.dataframe(mandi_list)

        # TAB 2: Nayi Sabji Add karne ka form
        with tab2:
            st.subheader("➕ Nayi Sabji ya Fruit Ka Name Jodein")
            with st.form("add_item_form", clear_on_submit=True):
                new_item_name = st.text_input("Nayi Sabji/Fruit Ka Naam Likhein (e.g., Bhindi, Gobhi, Seb):").strip()
                add_submit = st.form_submit_button("Add Item to List 📝")
                if add_submit and new_item_name:
                    if new_item_name in available_items:
                        st.warning("⚠️ Yeh naam pehle se list mein maujood hai.")
                    else:
                        payload = {"action": "add_item", "Item_Name": new_item_name}
                        try:
                            res = requests.post(SCRIPT_URL, data=json.dumps(payload))
                            if res.status_code == 200:
                                st.success(f"🎉 '{new_item_name}' ko list mein jod diya gaya hai! Ab managers ko ye option dikhega.")
                                st.rerun()
                        except:
                            st.error("❌ Add karne mein dikkat aayi.")

        # TAB 3: Today's Mandi Rates
        with tab3:
            st.subheader("📝 Mandi Se Aane Ke Baad Live Rate Update Karein")
            with st.form("rate_form"):
                updated_rates = {}
                for item in available_items:
                    updated_rates[item] = st.number_input(f"{item} Rate (₹):", min_value=0.0, value=st.session_state.mandi_rates.get(item, 0.0), step=1.0)
                rate_submit = st.form_submit_button("Save Today's Rates 💾")
                if rate_submit:
                    st.session_state.mandi_rates = updated_rates
                    st.success("🎉 Rates save ho gaye! Naye bills dekhne ke liye agla Tab kholein.")

        # TAB 4: Final Split Billing
        with tab4:
            st.subheader("💵 Mandi Rates Ke Hisab Se Final Bills")
            if df.empty or len(df) == 0:
                st.info("No data available.")
            else:
                calc_df = df.copy()
                calc_df["Qty"] = pd.to_numeric(calc_df["Qty"], errors='coerce').fillna(0)
                calc_df["Rate"] = calc_df["Item"].map(st.session_state.mandi_rates)
                calc_df["Total"] = calc_df["Qty"] * calc_df["Rate"]
                
                billing_list = calc_df.groupby("Mess")["Total"].sum().reset_index()
                st.dataframe(billing_list)
                
                if st.checkbox("Show Detailed Ledger"):
                    st.dataframe(calc_df)