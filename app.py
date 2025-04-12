import streamlit as st
import pandas as pd
from delivery_optimizer import optimize_route
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Streamlit page settings
st.set_page_config(
    page_title="🚛 Milk Run Optimizer Pro",
    page_icon="🚚",
    layout="wide"
)

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input(
        "OpenRouteService API Key",
        value=os.getenv("ORS_API_KEY", ""),
        type="password",
        help="Get your API key from https://openrouteservice.org/dev/#/signup"
    )
    os.environ["ORS_API_KEY"] = api_key

    st.markdown("---")
    st.markdown("### ℹ️ Instructions")
    st.markdown("""
    1. Enter addresses (one per line)  
    2. First address = warehouse/depot  
    3. Click 'Optimize Route'
    """)

# App title and subtitle
st.title("🚛 AI-Powered Milk Run Delivery Optimizer")
st.markdown("*Reduce delivery costs by up to 30% with optimized routes*")

# Address input section
with st.expander("📝 Enter Delivery Addresses", expanded=True):
    default_addresses = """Warehouse, 123 Main St, New York, NY
456 Elm St, Brooklyn, NY
789 Pine Rd, Queens, NY
321 Oak Ave, Manhattan, NY"""
    addresses = st.text_area(
        "Addresses (one per line):",
        value=default_addresses,
        height=150,
        label_visibility="collapsed"
    )

# Button to optimize
if st.button("✨ Optimize Route", type="primary", use_container_width=True):
    address_list = [addr.strip() for addr in addresses.split('\n') if addr.strip()]

    if len(address_list) < 2:
        st.error("❌ Need at least 2 addresses (depot + delivery)")
    else:
        with st.spinner("🚀 Calculating optimal route..."):
            try:
                route, total_distance, coords = optimize_route(address_list)

                if route:
                    st.success("✅ Route optimization complete!")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Distance", f"{total_distance/1000:.2f} km")
                    col2.metric("Delivery Stops", len(route) - 1)
                    col3.metric("Estimated Time", f"{(total_distance/1000)*2:.0f}-{(total_distance/1000)*3:.0f} min")

                    # Route table
                    with st.expander("📋 Route Sequence", expanded=True):
                        route_df = pd.DataFrame({
                            "Stop": [f"📍 {i+1}" for i in range(len(route))],
                            "Address": route,
                            "Type": ["🏭 Depot"] + ["📦 Delivery"] * (len(route) - 2) + ["🔙 Return"]
                        })
                        st.dataframe(
                            route_df,
                            use_container_width=True,
                            hide_index=True
                        )

                    # Map
                    with st.expander("🗺️ Route Visualization", expanded=True):
                        st.map(pd.DataFrame({
                            "lat": [c[0] for c in coords],
                            "lon": [c[1] for c in coords],
                            "size": [15] + [10] * (len(coords) - 1)
                        }))

                    # Download button
                    st.download_button(
                        "💾 Export as CSV",
                        route_df.to_csv(index=False),
                        "optimized_route.csv",
                        type="secondary"
                    )
                else:
                    st.error("⚠️ Optimization failed. Check addresses and API key.")

            except Exception as e:
                st.error(f"🔥 Critical Error: {str(e)}")
                st.markdown("""
                **Common fixes:**
                - Verify OpenRouteService API key
                - Check address formatting
                - Ensure internet connection
                - Try fewer addresses (API limits)
                """)

st.markdown("---")
st.caption("© 2023 Delivery Optimization AI | [Get ORS API Key](https://openrouteservice.org/dev/#/signup)")