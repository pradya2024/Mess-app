import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Page Configuration
st.set_page_config(page_title="Mess Supply Pro", page_icon="🥦", layout="centered")

# --- DATABASE CONNECTION (GOOGLE SHEET) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CUSTOM CSS FOR ANDROID FEEL ---
st.markdown("""
<style>
    .stApp { background-color: #F7F9FC; }
    .android-header {
        background: linear-gradient(135deg, #1E88E5, #1565C0);
        color: white; padding: 20px; border-radius: 15px;
        text-align: center; margin-bottom: 20px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    }
    .login-box {
        background-color: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-top: 20px;
    }
    .item-card {
        background-color: white; padding: 15px; border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 12px;
        border-left: 5px solid #4CAF50;
    }
    .bill-card {
        background-color: white; padding: 15px; border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 12px;
        border-left: 5px solid #FF9800;
    }
</style>
""", unsafe_allowed_html=True)

# --- LOGIN CREDENTIALS ---
USER_CREDENTIALS = {
    "admin": "admin123",
    "hq": "hq123", "rtt": "rtt123", "ffc": "ffc123", 
    "fc": "fc123", "so_s": "so123", "go_s": "go123", "veg_shop": "veg123"
}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""

rates = {"Aloo (Potato)": 30, "Tamatar (Tomato)": 40, "Pyaj (Onion)": 35, "Kela (Banana)": 50, "Seb (Apple)": 120}

st.markdown('<div class="android-header"><h1>📱 Mess Supply Pro</h1><p>Secure Demand & Billing</p></div>', unsafe_allowed_html=True)

if not st.session_state.logged_in:
    st.subheader("🔒 Login Karein")
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allowed_html=True)
        user_input = st.text_input("Username:").strip().lower()
        pass_input = st.text_input("Password:", type="password")
        login_btn = st.button("Login ✅", use_container_width=True)
        st.markdown('</div>', unsafe_allowed_html=True)
        
        if login_btn:
            if user_input in USER_CREDENTIALS and USER_CREDENTIALS[user_input] == pass_input:
                st.session_state.logged_in = True
                st.session_state.username = user_input
                st.rerun()
            else:
                st.error("❌ Galat Username ya Password!")
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

    try:
        existing_data = conn.read(ttl="5s")
        df = pd.DataFrame(existing_data)
    except:
        df = pd.DataFrame(columns=["Date", "Mess", "Item", "Qty", "Rate", "Total"])

    if st.session_state.username != "admin":
        st.subheader("📋 New Demand Form")
        current_mess = name_mapping[st.session_state.username]
        
        with st.form("demand_form", clear_on_submit=True):
            st.info(f"Aap **{current_mess}** ke liye demand daal rahe hain.")
            item = st.selectbox("Select Item:", list(rates.keys()))
            qty = st.number_input("Quantity (Kg / Dozen):", min_value=1.0, step=1.0)
            submit = st.form_submit_button("Submit Demand 🚀")
            
            if submit:
                rate = rates[item]
                total = qty * rate
                
                new_row = pd.DataFrame([{
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Mess": current_mess,
                    "Item": item,
                    "Qty": qty,
                    "Rate": rate,
                    "Total": total
                }])
                
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("✅ Success: Data Google Sheet mein save ho gaya!")
    else:
        tab1, tab2 = st.tabs(["🛒 Mandi Packing List", "💰 Mess Wise Bills"])
        
        if df.empty:
            st.info("Abhi tak kisi bhi mess ne demand nahi bheji hai.")
        else:
            with tab1:
                st.subheader("🛒 Mandi Purchase Consolidated List")
                mandi_list = df.groupby("Item")["Qty"].sum().reset_index()
                for idx, row in mandi_list.iterrows():
                    st.markdown(f"""
                    <div class="item-card">
                        <span style="font-size:18px; font-weight:bold; color:#333;">{row['Item']}</span><br>
                        <span style="color:#666;">Total Weight Needed:</span> 
                        <span style="font-size:18px; font-weight:bold; color:#4CAF50;">{row['Qty']} Kg/Dozen</span>
                    </div>
                    """, unsafe_allowed_html=True)

            with tab2:
                st.subheader("💰 Live Mess Wise Bills")
                billing_list = df.groupby("Mess")["Total"].sum().reset_index()
                for idx, row in billing_list.iterrows():
                    st.markdown(f"""
                    <div class="bill-card">
                        <span style="font-size:18px; font-weight:bold; color:#333;">🏢 {row['Mess']}</span><br>
                        <span style="color:#666;">Current Bill Amount:</span> 
                        <span style="font-size:18px; font-weight:bold; color:#FF9800;">₹{row['Total']}</span>
                    </div>
                    """, unsafe_allowed_html=True)
                
                if st.checkbox("Show Full Ledger View"):
                    st.dataframe(df)
