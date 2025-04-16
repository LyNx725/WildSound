
import streamlit as st
import requests
import time
import numpy as np
import pandas as pd
from monitor import WildlifeMonitor
import plotly.graph_objects as go
import streamlit as st
import time
import numpy as np
import pandas as pd
from monitor import WildlifeMonitor
import plotly.graph_objects as go


if "email" not in st.session_state:
    st.session_state["email"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "register" 
st.set_page_config(page_title="Wildlife Monitor", layout="wide")

# Initialize the monitor
if 'monitor' not in st.session_state:
    user_email = st.session_state.get("email", None)
    st.session_state.monitor = WildlifeMonitor()
    st.session_state.volume_history = []
    st.session_state.alert_history = []

def update_volume_chart():
    fig = go.Figure()

    # Plot the volume history as a line
    fig.add_trace(go.Scatter(
        y=st.session_state.volume_history,
        mode='lines',
        name='Volume Level',
        line=dict(color='blue')  # Regular line color (default)
    ))

    # Add a red horizontal line for the threshold
    fig.add_hline(y=st.session_state.monitor.threshold, line_color='red', line_dash='dash')

    # Highlight the point of the alert (if any)
    if len(st.session_state.alert_history) > 0:
        # If an alert occurred, get the latest alert time (we can get this from the alert history)
        alert_time = st.session_state.alert_history[-1]['timestamp']
        alert_index = len(st.session_state.volume_history) - 1  # Assuming alert is the latest data point

        # Add a vertical red line to mark the alert
        fig.add_vline(x=alert_index, line_color='red', line_dash='dot', annotation_text="ALERT", annotation_position="top right")

    fig.update_layout(
        title='Real-time Audio Levels',
        xaxis_title='Time',
        yaxis_title='Volume',
        showlegend=True
    )

    return fig


# UI Layout
st.title("Wildlife Sound Monitor")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Monitor Controls")
    threshold = st.slider("Alert Threshold", 0, 1000, int(st.session_state.monitor.threshold))
    st.session_state.monitor.threshold = threshold
    
    if st.button("Start Monitoring" if not st.session_state.monitor.is_monitoring else "Stop Monitoring"):
        if st.session_state.monitor.is_monitoring:
            st.session_state.monitor.stop_stream()
        else:
            st.session_state.monitor.start_stream()

with col2:
    st.subheader("Current Status")
    status = st.empty()
    volume_chart = st.empty()

# Alerts section
st.subheader("Alert History")
alerts_container = st.container()

# Main monitoring loop
while st.session_state.monitor.is_monitoring:
    current_volume = st.session_state.monitor.get_current_volume()
    st.session_state.volume_history.append(current_volume)
    
    # Keep only last 100 readings
    if len(st.session_state.volume_history) > 100:
        st.session_state.volume_history.pop(0)
    
    # Update status
    status.metric("Current Volume Level", f"{int(current_volume)}")
    volume_chart.plotly_chart(update_volume_chart(), use_container_width=True)
    
    # Check for alerts
    if current_volume > threshold:
        file_path = st.session_state.monitor.record_audio()
        alert = st.session_state.monitor.analyze_audio(file_path)
        st.session_state.alert_history.append(alert)
        
        with alerts_container:
            for alert in reversed(st.session_state.alert_history):
                st.write(f"*Alert at {alert['timestamp']}*")
                st.write(f"File: {alert['file']}")
                st.write(alert['analysis'])
                st.divider()
    
    time.sleep(0.1)
  

# Show stopped status when not monitoring
if not st.session_state.monitor.is_monitoring:
    status.warning("Monitoring Stopped")