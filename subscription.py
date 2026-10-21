import streamlit as st
import time
import auth
from i18n import _ # <--- Import the translation function

def show():
    """
    Renders the Subscription/Upgrade Page
    """
    st.markdown(f"""
    <div class="subscription-page">
        <div class="subscription-header">
            <div>
                <span class="subscription-kicker">{_('Plans')}</span>
                <h4 class="subscription-hero">{_('Scale Your Product Intelligence')}</h4>
                <p class="subscription-subtitle">{_('Choose the plan that unlocks the highest-value AI review insights for your team.')}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    current_plan = st.session_state.user_info.get('plan', 'free')
    
    c1, c2 = st.columns(2)
    
    # 1. BASIC PLAN
    with c1:
        st.markdown(f"""
        <div class="subscription-card subscription-card-basic">
            <div class="subscription-card-head">
                <div>
                    <div class="subscription-card-topline">{_('For growing teams')}</div>
                    <h3 class="subscription-plan">{_('BASIC')}</h3>
                </div>
                <div class="subscription-plan-icon">B</div>
            </div>
            <div class="subscription-price">MYR 48.99<span>/mo</span></div>
            <p class="subscription-card-copy">{_('Core review analytics for smaller product teams.')}</p>
            <hr>
            <ul class="subscription-features">
                <li><span class="feature-icon good">✓</span><span>{_('500 Rows Analysis')}</span></li>
                <li><span class="feature-icon good">✓</span><span>{_('Basic Charts')}</span></li>
                <li><span class="feature-icon good">✓</span><span>{_('PDF Export')}</span></li>
                <li><span class="feature-icon good">✓</span><span>{_('API Integration')}</span></li>
                <li><span class="feature-icon bad">×</span><span>{_('Real-time Monitor')}</span></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if current_plan == 'basic':
            st.button(_("Current Plan"), disabled=True, key="btn_basic", use_container_width=True)
        else:
            lbl = _("Downgrade to Basic") if current_plan == 'premium' else _("Upgrade to Basic")
            if st.button(lbl, type="secondary", key="btn_basic", use_container_width=True):
                with st.spinner(_("Processing Payment...")):
                    time.sleep(1)
                    auth.upgrade_user_plan(st.session_state.user_info['username'], 'basic')
                    st.session_state.user_info['plan'] = 'basic'
                    st.toast(_("🎉 Plan updated to Basic!"), icon="✅")
                    time.sleep(1)
                    st.rerun()

    # 2. PREMIUM PLAN
    with c2:
        st.markdown(f"""
        <div class="subscription-card subscription-card-premium">
            <div class="subscription-card-head">
                <div>
                    <div class="subscription-card-topline">{_('Best for full insights')}</div>
                    <h3 class="subscription-plan">{_('PREMIUM')}</h3>
                </div>
                <div class="subscription-plan-icon premium">P</div>
            </div>
            <div class="subscription-price">MYR 99.99<span>/mo</span></div>
            <p class="subscription-card-copy">{_('Advanced reporting and monitoring for active teams.')}</p>
            <hr>
            <ul class="subscription-features">
                <li><span class="feature-icon good">✓</span><span>{_('Unlimited Analysis')}</span></li>
                <li><span class="feature-icon good">✓</span><span>{_('Advanced Charts')}</span></li>
                <li><span class="feature-icon good">✓</span><span>{_('PDF & Excel Export')}</span></li>
                <li><span class="feature-icon good">✓</span><span>{_('API Integration')}</span></li>
                <li><span class="feature-icon good">✓</span><span>{_('Real-time Monitor')}</span></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if current_plan == 'premium':
            st.button(_("Current Plan"), disabled=True, key="btn_prem", use_container_width=True)
        else:
            if st.button(_("Upgrade to Premium"), type="primary", key="btn_prem", use_container_width=True):
                with st.spinner(_("Processing Payment...")):
                    time.sleep(1.5)
                    auth.upgrade_user_plan(st.session_state.user_info['username'], 'premium')
                    st.session_state.user_info['plan'] = 'premium'
                    st.toast(_("🚀 Welcome to Premium!"), icon="💎")
                    time.sleep(1)
                    st.rerun()