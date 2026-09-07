import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# Page Configuration
st.set_page_config(page_title="ANNAPURNA VEGETABLE SHOP", page_icon="🥦", layout="centered")

# --- CUSTOM CSS FOR SHOP BRANDING & BLACK TEXT VISIBILITY (LIGHT & DARK MODE) ---
st.markdown("""
<style>
    /* Sabhi normal text, tab, labels ko hamesha visible rakhne ke liye */
    .stApp, p, label, .stMarkdown, .stSelectbox, div[data-baseweb="select"] {
        color: #222222 !important;
    }
    .shop-header {
        background: linear-gradient(135deg, #FF9800, #F57C00);
        color: white !important; padding: 25px; border-radius: 15px;
        text-align: center; margin-bottom: 25px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
    }
    .shop-header h1 { color: white !important; font-size: 28px !important; font-weight: bold !important; margin: 0; }
    .shop-header p { color: #FFF3E0 !important; font-size: 16px !important; margin: 5px 0 0 0; }
    
    /* Tabs ke text ko zabardasti bold aur visible karne ke liye */
    button[data-baseweb="tab"] p {
        color: #111111 !important;
        font-weight: bold !important;
        font-size: 15px !important;
    }
    button[aria-selected="true"] p {
        color: #E65100 !important;
        border-bottom: 2px solid #E65100;
    }
</style>
""", unsafe_allow_html=True)

# 🟢 APNI GOOGLE WEB APP KI LINK YAHAN PASTE KAREIN
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxbbUBdxj__qToZfF33nT2E3E464K9i3v6S9vDSaxLx4ll8nwNrY8gDaDQqN2sfJbQ2/exec"

# Shop Main Banner on Top
st.markdown('<div class="shop-header"><h1>🚩 ANNAPURNA VEGETABLE SHOP</h1><p>Mess Supply Demand & Billing System</p></div>', unsafe_allow_html=True)

# --- LOGIN CREDENTIALS ---
USER_CREDENTIALS = {
    "admin": "admin123",
    "hq": "hq123", "rtt": "rtt123", "ffc": "ffc123", 
    "fc": "fc123", "so_s": "so123", "go_s": "go123", "veg_shop": "veg123"
}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'mandi_rates' not in st.session_state: st.session_state.mandi_rates = {}

# Google Script API se live database load karna
try:
    response = requests.get(SCRIPT_URL, timeout=5)
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
                        st.error(f"⚠️ Server Error! Status Code: {res.status_code}")
                except Exception as e:
                    st.error(f"❌ Connection Error: {str(e)}")
                
    # ---- 📊 ADMIN (OWNER) LOGGED IN ----
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["🛒 Mandi Packing List", "➕ Add New Sabji/Fruit", "💰 Today's Mandi Rates", "💵 Alag-Alag Mess Bills"])
        
        # TAB 1: Packing List
        with tab1:
            st.subheader("🛒 Mandi Purchase Consolidated List")
            if df.empty or len(df) == 0:
                st.info("Abhi tak kisi bhi mess ne demand nahi bheji hai.")
            else:
                df["Qty"] = pd.to_numeric(df["Qty"], errors='coerce').fillna(0)
                mandi_list = df.groupby("Item")["Qty"].sum().reset_index()
                mandi_list.index = mandi_list.index + 1
                st.dataframe(mandi_list)

        # TAB 2: Nayi Sabji Add
        with tab2:
            st.subheader("➕ Nayi Sabji ya Fruit Ka Name Jodein")
            with st.form("add_item_form", clear_on_submit=True):
                new_item_name = st.text_input("Nayi Sabji/Fruit Ka Naam Likhein:").strip()
                add_submit = st.form_submit_button("Add Item to List 📝")
                if add_submit and new_item_name:
                    if new_item_name in available_items:
                        st.warning("⚠️ Yeh naam pehle se list mein maujood hai.")
                    else:
                        payload = {"action": "add_item", "Item_Name": new_item_name}
                        try:
                            res = requests.post(SCRIPT_URL, data=json.dumps(payload))
                            if res.status_code == 200:
                                st.success(f"🎉 '{new_item_name}' ko list mein jod diya gaya hai!")
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

        # TAB 4: Final Split Billing with Download Option
        with tab4:
            st.subheader("💵 Alag-Alag Mess Wise Final Bills")
            if df.empty or len(df) == 0:
                st.info("No data available.")
            else:
                calc_df = df.copy()
                calc_df["Qty"] = pd.to_numeric(calc_df["Qty"], errors='coerce').fillna(0)
                calc_df["Rate"] = calc_df["Item"].map(st.session_state.mandi_rates).fillna(0)
                calc_df["Total"] = calc_df["Qty"] * calc_df["Rate"]
                
                # --- SUMMARY OVERVIEW ---
                st.write("📊 **Sabhi Mess Ka Total Kharcha:**")
                summary_df = calc_df.groupby("Mess")["Total"].sum().reset_index()
                summary_df.columns = ["Mess Name", "Total Bill (₹)"]
                summary_df.index = summary_df.index + 1
                st.dataframe(summary_df)
                
                st.markdown("---")
                
                # --- SEPARATE MESS FILTER & DOWNLOAD ---
                st.write("🔍 **Kisi Ek Mess Ka Detail Bill Dekhein & Download Karein:**")
                unique_messes = calc_df["Mess"].unique()
                selected_mess = st.selectbox("Mess Chunein:", unique_messes)
                
                # Filter data for selected mess
                mess_bill_df = calc_df[calc_df["Mess"] == selected_mess][["Date", "Item", "Qty", "Rate", "Total"]].reset_index(drop=True)
                mess_bill_df.index = mess_bill_df.index + 1
                
                st.markdown(f"## 📋 ANNAPURNA VEGETABLE SHOP")
                st.markdown(f"### 🏢 FINAL BILL FOR MESS: **{selected_mess}**")
                
                # Total Bill Amount Metric
                mess_total = mess_bill_df["Total"].sum()
                st.metric(label=f"Total Bill Amount ({selected_mess})", value=f"₹{mess_total:,.2f}")
                
                # --- 🚩 NEW FIX 1: DOWNLOAD BUTTON KO TABLE SE PEHLE (TOP PAR) LAGAYA HAI ---
                # Isse table side scroll ho bhi jaye toh bhi button ekdam samne dikhega hide nahi hoga
