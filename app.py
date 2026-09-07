import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# Page Configuration
st.set_page_config(page_title="Mess Supply Pro", page_icon="🥦", layout="centered")

# 🟢 APNI GOOGLE WEB APP KI LINK YAHAN DAALEIN
# Jo lambi URL link aapne copy ki hai, use niche ke dono quotes "" ke beech mein paste karein
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby9KFYaonjtoug4uN4d_iZyQG4F8Z0POv6gTfpdSwgC5k-CHHm70PLvwlveR7NNJUaB/exec"

st.title("📱 Mess Supply Pro")
st.write("Secure Demand & Billing System")

# --- LOGIN CREDENTIALS ---
USER_CREDENTIALS = {
    "admin": "admin123",
    "hq": "hq123", "rtt": "rtt123", "ffc": "ffc123", 
    "fc": "fc123", "so_s": "so123", "go_s": "go123", "veg_shop": "veg123"
}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""

rates = {"Aloo (Potato)": 30, "Tamatar (Tomato)": 40, "Pyaj (Onion)": 35, "Kela (Banana)": 50, "Seb (Apple)": 120}

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

    # Google Script API se live data load karna
    try:
        response = requests.get(SCRIPT_URL)
        raw_data = response.json()
        if raw_data and len(raw_data) > 0:
            df = pd.DataFrame(raw_data)
        else:
            df = pd.DataFrame(columns=["Date", "Mess", "Item", "Qty", "Rate", "Total"])
    except:
        df = pd.DataFrame(columns=["Date", "Mess", "Item", "Qty", "Rate", "Total"])

    # ---- 🟢 MESS MANAGER LOGGED IN ----
    if st.session_state.username != "admin":
        st.subheader("📋 New Demand Form")
        current_mess = name_mapping[st.session_state.username]
        st.info(f"Aap {current_mess} ke liye demand daal rahe hain.")
        
        with st.form("demand_form", clear_on_submit=True):
            item = st.selectbox("Select Item:", list(rates.keys()))
            qty = st.number_input("Quantity (Kg / Dozen):", min_value=1.0, step=1.0)
            submit = st.form_submit_button("Submit Demand 🚀")
            
            if submit:
                rate = rates[item]
                total = qty * rate
                
                payload = {
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Mess": current_mess,
                    "Item": item,
                    "Qty": qty,
                    "Rate": rate,
                    "Total": total
                }
                
                try:
                    res = requests.post(SCRIPT_URL, data=json.dumps(payload))
                    if res.status_code == 200:
                        st.success("✅ Success: Data Google Sheet mein save ho gaya!")
                        st.balloons()
                    else:
                        st.error("⚠️ Server problem: Data save nahi hua.")
                except:
                    st.error("❌ Connection Error: Data send nahi ho paya.")
                
    # ---- 📊 ADMIN (OWNER) LOGGED IN ----
    else:
        tab1, tab2 = st.tabs(["🛒 Mandi Packing List", "💰 Mess Wise Bills"])
        
        if df.empty or len(df) == 0:
            st.info("Abhi tak kisi bhi mess ne demand nahi bheji hai.")
        else:
            with tab1:
                st.subheader("🛒 Mandi Purchase Consolidated List")
                df["Qty"] = pd.to_numeric(df["Qty"], errors='coerce').fillna(0)
                mandi_list = df.groupby("Item")["Qty"].sum().reset_index()
                st.dataframe(mandi_list)

            with tab2:
                st.subheader("💰 Live Mess Wise Bills")
                df["Total"] = pd.to_numeric(df["Total"], errors='coerce').fillna(0)
                billing_list = df.groupby("Mess")["Total"].sum().reset_index()
                st.dataframe(billing_list)
                
                if st.checkbox("Show Full Ledger View"):
                    st.dataframe(df)
