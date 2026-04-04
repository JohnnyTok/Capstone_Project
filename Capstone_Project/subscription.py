import streamlit as st
import time
import auth

def show():
    """
    Renders the Subscription/Upgrade Page
    """
    st.title("💎 Upgrade Your Plan")
    st.markdown("Unlock the full potential of your AI analytics.")
    
    current_plan = st.session_state.user_info.get('plan', 'free')
    
    c1, c2 = st.columns(2)
    
    # 1. BASIC PLAN
    with c1:
        st.markdown("""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-top: 5px solid #00C853; text-align: center; height: 400px;">
            <h3 style="color: #00C853;">BASIC</h3>
            <h1 style="color: white;">MYR 48.99<span style="font-size: 16px; color: #888;">/mo</span></h1>
            <hr style="border-color: #333;">
            <ul style="text-align: left; color: #ddd; list-style-type: none; padding: 0;">
                <li>✅ 500 Rows Analysis</li>
                <li>✅ Basic Charts</li>
                <li>✅ PDF Export</li>
                <li>✅ API Integration</li>
                <li>❌ Real-time Monitor</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if current_plan == 'basic':
            st.button("Current Plan", disabled=True, key="btn_basic", use_container_width=True)
        else:
            lbl = "Downgrade to Basic" if current_plan == 'premium' else "Upgrade to Basic"
            if st.button(lbl, type="secondary", key="btn_basic", use_container_width=True):
                with st.spinner("Processing Payment..."):
                    time.sleep(1)
                    auth.upgrade_user_plan(st.session_state.user_info['username'], 'basic')
                    st.session_state.user_info['plan'] = 'basic'
                    st.toast("🎉 Plan updated to Basic!", icon="✅")
                    time.sleep(1)
                    st.rerun()

    # 2. PREMIUM PLAN
    with c2:
        st.markdown("""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-top: 5px solid #FFD700; text-align: center; height: 400px; box-shadow: 0 0 20px rgba(255, 215, 0, 0.2);">
            <h3 style="color: #FFD700;">PREMIUM</h3>
            <h1 style="color: white;">MYR 99.99<span style="font-size: 16px; color: #888;">/mo</span></h1>
            <hr style="border-color: #333;">
            <ul style="text-align: left; color: #ddd; list-style-type: none; padding: 0;">
                <li>✅ Unlimited Analysis</li>
                <li>✅ Advanced Charts</li>
                <li>✅ PDF & Excel Export</li>
                <li>✅ API Integration</li>
                <li>✅ Real-time Monitor</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if current_plan == 'premium':
            st.button("Current Plan", disabled=True, key="btn_prem", use_container_width=True)
        else:
            if st.button("Upgrade to Premium", type="primary", key="btn_prem", use_container_width=True):
                with st.spinner("Processing Payment..."):
                    time.sleep(1.5)
                    auth.upgrade_user_plan(st.session_state.user_info['username'], 'premium')
                    st.session_state.user_info['plan'] = 'premium'
                    st.toast("🚀 Welcome to Premium!", icon="💎")
                    time.sleep(1)
                    st.rerun()
