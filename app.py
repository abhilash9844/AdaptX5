"""
AI Infrastructure Efficiency Optimizer - Dashboard
===================================================
Professional Streamlit dashboard for real-time infrastructure monitoring
and AI-powered optimization.

Usage:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import time
from collections import deque
from typing import Optional, Dict, List

# Import custom modules
from utils.simulation import InfrastructureSimulator
from utils.server_manager import ServerManager
from utils.optimizer import AIOptimizer
from utils.alarm import TemperatureAlarm


# ===== PAGE CONFIGURATION =====
st.set_page_config(
    page_title="AI Infrastructure Optimizer",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ===== CUSTOM CSS STYLING =====
def load_custom_css():
    """Load custom CSS for professional appearance."""
    st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 1rem;
    }
    
    /* Metric card styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .metric-card-success {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .metric-card-warning {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .metric-card-danger {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
    }
    
    /* Server status badges */
    .server-on {
        background-color: #28a745;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.25rem;
    }
    
    .server-off {
        background-color: #dc3545;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.25rem;
    }
    
    /* Title styling */
    .main-title {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem 0;
    }
    
    /* Suggestion cards */
    .suggestion-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* Status indicator */
    .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    
    .status-good { background-color: #28a745; }
    .status-warning { background-color: #ffc107; }
    .status-critical { background-color: #dc3545; }
    
    /* Action card */
    .action-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        margin: 1rem 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


# ===== MODEL LOADING =====
@st.cache_resource
def load_ml_model():
    """Load the trained ML model and scaler."""
    model_path = 'models/efficiency_model.pkl'
    scaler_path = 'models/scaler.pkl'
    
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        st.error("⚠️ Model files not found! Please run train_model.py first.")
        return None, None
    
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    
    return model, scaler


# ===== SESSION STATE INITIALIZATION =====
def init_session_state():
    """Initialize all session state variables."""
    
    # Simulator
    if 'simulator' not in st.session_state:
        st.session_state.simulator = InfrastructureSimulator(initial_servers=4)
    
    # Server manager
    if 'server_manager' not in st.session_state:
        st.session_state.server_manager = ServerManager()
    
    # AI optimizer
    if 'optimizer' not in st.session_state:
        st.session_state.optimizer = AIOptimizer()
    
    # Temperature alarm
    if 'alarm' not in st.session_state:
        st.session_state.alarm = TemperatureAlarm(threshold=42.0)
    
    # History buffers for graphs (store last 50 points)
    if 'history' not in st.session_state:
        st.session_state.history = {
            'time': deque(maxlen=50),
            'workload': deque(maxlen=50),
            'energy': deque(maxlen=50),
            'temperature': deque(maxlen=50),
            'efficiency': deque(maxlen=50),
            'cpu': deque(maxlen=50)
        }
    
    # Time counter
    if 'time_counter' not in st.session_state:
        st.session_state.time_counter = 0
    
    # Last AI action
    if 'last_ai_action' not in st.session_state:
        st.session_state.last_ai_action = None
    
    # Current state
    if 'current_state' not in st.session_state:
        st.session_state.current_state = None


# ===== PREDICTION FUNCTION =====
def predict_efficiency(model, scaler, state: Dict) -> float:
    """
    Predict efficiency using the trained model - FIXED.
    """
    if model is None or scaler is None:
        # Use the corrected fallback calculation
        workload = state['workload']
        servers = state['servers']
        cpu = state.get('cpu', workload)
        energy = state.get('energy', 100)
        
        # Corrected formula matching the simulation
        optimal_per_server = 30.0
        actual_per_server = workload / max(servers, 1)
        utilization_ratio = actual_per_server / optimal_per_server
        
        if utilization_ratio <= 1.0:
            base_efficiency = utilization_ratio * 85
        else:
            over_ratio = min(utilization_ratio - 1.0, 1.0)
            base_efficiency = 85 - (over_ratio * 25)
        
        return min(92, max(20, base_efficiency))
    
    # Prepare features
    features = np.array([[
        state['servers'],
        state['workload'],
        state['cpu'],
        state['energy'],
        state['temperature']
    ]])
    
    # Scale and predict
    features_scaled = scaler.transform(features)
    prediction = model.predict(features_scaled)[0]
    
    # Clip to valid range (NEVER exceed 92%)
    return min(92.0, max(20.0, prediction))

# ===== UPDATE SIMULATION =====
def update_simulation(model, scaler):
    """Update simulation state and perform AI optimization."""
    
    sim = st.session_state.simulator
    server_mgr = st.session_state.server_manager
    optimizer = st.session_state.optimizer
    alarm = st.session_state.alarm
    history = st.session_state.history
    
    # Sync servers between simulator and manager
    sim.set_servers(server_mgr.active_count)
    
    # Get new state
    state = sim.step()
    st.session_state.current_state = state
    
    # Predict efficiency
    efficiency = predict_efficiency(model, scaler, state)
    state['efficiency'] = efficiency
    
    # Update time
    st.session_state.time_counter += 1
    
    # Update history
    history['time'].append(st.session_state.time_counter)
    history['workload'].append(state['workload'])
    history['energy'].append(state['energy'])
    history['temperature'].append(state['temperature'])
    history['efficiency'].append(efficiency)
    history['cpu'].append(state['cpu'])
    
    # Check temperature alarm
    alarm.check_and_trigger(state['temperature'])
    
    # AI optimization decision
    st.session_state.last_ai_action = None
    
    if server_mgr.can_shutdown(state['workload']):
        # Simulate efficiency after potential shutdown
        simulated_state = state.copy()
        simulated_state['servers'] = server_mgr.active_count - 1
        predicted_after = predict_efficiency(model, scaler, simulated_state)
        
        decision = server_mgr.decide_shutdown(
            state,
            efficiency,
            predicted_after
        )
        
        if decision.should_shutdown and decision.target_server:
            server_mgr.execute_shutdown(decision.target_server)
            st.session_state.last_ai_action = server_mgr.get_last_action()
            sim.set_servers(server_mgr.active_count)
    
    # Generate optimization suggestions
    suggestions = optimizer.analyze(
        state['servers'],
        state['workload'],
        state['cpu'],
        state['energy'],
        state['temperature'],
        efficiency
    )
    
    return state, efficiency, suggestions


# ===== RENDER FUNCTIONS =====
def render_header():
    """Render the dashboard header."""
    st.markdown("""
    <h1 style='text-align: center; color: #667eea;'>
        🖥️ AI Infrastructure Efficiency Optimizer
    </h1>
    <p style='text-align: center; color: #666; margin-bottom: 2rem;'>
        Real-time monitoring and AI-powered optimization for data center efficiency
    </p>
    """, unsafe_allow_html=True)


def render_metrics(state: Dict, efficiency: float):
    """Render the main metrics section."""
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            label="🖥️ Active Servers",
            value=f"{state['servers']}/4",
            delta=None
        )
    
    with col2:
        st.metric(
            label="📊 Workload",
            value=f"{state['workload']:.1f}%",
            delta=None
        )
    
    with col3:
        st.metric(
            label="⚡ CPU Usage",
            value=f"{state['cpu']:.1f}%",
            delta=None
        )
    
    with col4:
        st.metric(
            label="🔋 Energy",
            value=f"{state['energy']:.1f}W",
            delta=None
        )
    
    with col5:
        temp_color = "normal" if state['temperature'] < 38 else ("inverse" if state['temperature'] >= 42 else "off")
        st.metric(
            label="🌡️ Temperature",
            value=f"{state['temperature']:.1f}°C",
            delta=None
        )
    
    with col6:
        eff_delta = "normal" if efficiency >= 60 else "inverse"
        st.metric(
            label="📈 Efficiency",
            value=f"{efficiency:.1f}%",
            delta=None
        )


def render_efficiency_gauge(efficiency: float):
    """Render a large efficiency display."""
    
    # Determine color based on efficiency
    if efficiency >= 70:
        color = "#28a745"  # Green
        status = "Excellent"
    elif efficiency >= 50:
        color = "#ffc107"  # Yellow
        status = "Good"
    else:
        color = "#dc3545"  # Red
        status = "Needs Improvement"
    
    st.markdown(f"""
    <div style='
        background: linear-gradient(135deg, {color}22 0%, {color}44 100%);
        border: 3px solid {color};
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    '>
        <h2 style='color: {color}; margin: 0;'>AI Predicted Efficiency</h2>
        <h1 style='font-size: 4rem; color: {color}; margin: 0;'>{efficiency:.1f}%</h1>
        <p style='color: {color}; font-size: 1.2rem;'>{status}</p>
    </div>
    """, unsafe_allow_html=True)


def render_server_status(server_manager: ServerManager):
    """Render server status indicators."""
    
    st.subheader("🖥️ Server Status")
    
    cols = st.columns(4)
    
    for i, (name, is_active) in enumerate(server_manager.get_server_display()):
        with cols[i]:
            if is_active:
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                    padding: 1rem;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
                '>
                    <h4 style='margin: 0;'>{name}</h4>
                    <p style='margin: 0.5rem 0 0 0; font-size: 1.5rem;'>🟢 ON</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                    color: white;
                    padding: 1rem;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
                '>
                    <h4 style='margin: 0;'>{name}</h4>
                    <p style='margin: 0.5rem 0 0 0; font-size: 1.5rem;'>🔴 OFF</p>
                </div>
                """, unsafe_allow_html=True)


def render_ai_action(action: Optional[str]):
    """Render the AI action notification."""
    
    st.subheader("🤖 AI Action")
    
    if action:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        '>
            <h3 style='margin: 0;'>🎯 {action}</h3>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("✅ No automated actions taken - system is optimal")


def render_suggestions(suggestions: List):
    """Render AI optimization suggestions - FIXED."""
    
    st.subheader("💡 AI Suggestions")
    
    if not suggestions:
        st.success("✅ System operating optimally - no suggestions")
        return
    
    # Priority colors
    priority_colors = {
        'CRITICAL': ('#dc3545', '#fff5f5'),  # Red
        'HIGH': ('#fd7e14', '#fff8f0'),       # Orange
        'MEDIUM': ('#ffc107', '#fffbeb'),     # Yellow
        'LOW': ('#28a745', '#f0fff4'),        # Green
        'INFO': ('#17a2b8', '#f0f9ff')        # Blue
    }
    
    for suggestion in suggestions[:6]:  # Show top 6
        priority_name = suggestion.priority.name
        text_color, bg_color = priority_colors.get(priority_name, ('#6c757d', '#f8f9fa'))
        
        # Get the display text with icon
        if hasattr(suggestion, 'get_display_text'):
            display_text = suggestion.get_display_text()
        elif hasattr(suggestion, 'icon') and suggestion.icon:
            display_text = f"{suggestion.icon} {suggestion.message}"
        else:
            display_text = suggestion.message
        
        st.markdown(f"""
        <div style='
            background: {bg_color};
            border-left: 4px solid {text_color};
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 0 8px 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        '>
            <span style='
                color: {text_color}; 
                font-weight: bold;
                font-size: 0.85em;
                background: {text_color}22;
                padding: 2px 8px;
                border-radius: 4px;
                margin-right: 8px;
            '>{priority_name}</span>
            <span style='color: #333;'>{display_text}</span>
        </div>
        """, unsafe_allow_html=True)

def render_graphs():
    """Render real-time graphs."""
    
    history = st.session_state.history
    
    if len(history['time']) < 2:
        st.info("📊 Collecting data... graphs will appear shortly")
        return
    
    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Time': list(history['time']),
        'Workload (%)': list(history['workload']),
        'Energy (W)': list(history['energy']),
        'Temperature (°C)': list(history['temperature']),
        'Efficiency (%)': list(history['efficiency']),
        'CPU (%)': list(history['cpu'])
    })
    
    # Two columns for graphs
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Workload & CPU")
        chart_data = df[['Time', 'Workload (%)', 'CPU (%)']].set_index('Time')
        st.line_chart(chart_data, height=250)
        
        st.subheader("🔋 Energy Consumption")
        chart_data = df[['Time', 'Energy (W)']].set_index('Time')
        st.line_chart(chart_data, height=250)
    
    with col2:
        st.subheader("🌡️ Temperature")
        chart_data = df[['Time', 'Temperature (°C)']].set_index('Time')
        st.line_chart(chart_data, height=250)
        
        st.subheader("📈 Efficiency Trend")
        chart_data = df[['Time', 'Efficiency (%)']].set_index('Time')
        st.line_chart(chart_data, height=250)


def render_sidebar():
    """Render the sidebar controls."""
    
    st.sidebar.header("⚙️ Control Panel")
    
    # Manual server control
    st.sidebar.subheader("Server Control")
    
    server_mgr = st.session_state.server_manager
    
    for server_id, server in server_mgr.servers.items():
        col1, col2 = st.sidebar.columns([2, 1])
        with col1:
            st.write(f"{server.name}")
        with col2:
            if st.button(
                "ON" if not server.is_active else "OFF",
                key=f"toggle_{server_id}",
                type="primary" if not server.is_active else "secondary"
            ):
                if server.is_active:
                    server_mgr.execute_shutdown(server_id)
                else:
                    server_mgr.activate_server(server_id)
    
    st.sidebar.divider()
    
    # Settings
    st.sidebar.subheader("Alarm Settings")
    threshold = st.sidebar.slider(
        "Temperature Threshold (°C)",
        min_value=35.0,
        max_value=50.0,
        value=st.session_state.alarm.threshold,
        step=0.5
    )
    st.session_state.alarm.set_threshold(threshold)
    
    # Reset button
    st.sidebar.divider()
    if st.sidebar.button("🔄 Reset Simulation", type="secondary"):
        st.session_state.simulator.reset()
        st.session_state.server_manager.reset()
        st.session_state.history = {
            'time': deque(maxlen=50),
            'workload': deque(maxlen=50),
            'energy': deque(maxlen=50),
            'temperature': deque(maxlen=50),
            'efficiency': deque(maxlen=50),
            'cpu': deque(maxlen=50)
        }
        st.session_state.time_counter = 0
        st.session_state.last_ai_action = None
        st.rerun()
    
    # System info
    st.sidebar.divider()
    st.sidebar.subheader("ℹ️ System Info")
    st.sidebar.write(f"Update Interval: 2 seconds")
    st.sidebar.write(f"Data Points: {len(st.session_state.history['time'])}/50")
    st.sidebar.write(f"Time Steps: {st.session_state.time_counter}")


def render_alarm_status(alarm: TemperatureAlarm, temperature: float):
    """Render alarm status."""
    status = alarm.get_status(temperature)
    
    if "CRITICAL" in status or "ALARM" in status:
        st.error(status)
    elif "WARNING" in status:
        st.warning(status)
    else:
        st.success(status)


# ===== MAIN APPLICATION =====
def main():
    """Main application entry point."""
    
    # Load CSS
    load_custom_css()
    
    # Initialize session state
    init_session_state()
    
    # Load ML model
    model, scaler = load_ml_model()
    
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar()
    
    # Update simulation
    state, efficiency, suggestions = update_simulation(model, scaler)
    
    # Main layout
    st.divider()
    
    # Metrics row
    render_metrics(state, efficiency)
    
    st.divider()
    
    # Main content columns
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Efficiency gauge
        render_efficiency_gauge(efficiency)
        
        # Server status
        render_server_status(st.session_state.server_manager)
        
        # Alarm status
        st.subheader("🚨 Alarm Status")
        render_alarm_status(st.session_state.alarm, state['temperature'])
        
        # AI Action
        render_ai_action(st.session_state.last_ai_action)
        
        # Suggestions
        render_suggestions(suggestions)
    
    with col2:
        # Real-time graphs
        st.subheader("📈 Real-Time Monitoring")
        render_graphs()
    
    # Auto-refresh
    time.sleep(2)
    st.rerun()


if __name__ == "__main__":
    main()