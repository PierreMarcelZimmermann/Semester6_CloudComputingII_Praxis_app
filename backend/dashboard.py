import streamlit as st
import os

# Set the title of the app
st.title("SkySight Log Dashboard")

# Description of the app
st.write("""
    This dashboard allows you to view and filter log entries from the `app.log` file.
    You can filter the logs by different log levels (INFO, ERROR, DEBUG) and see the logs in real-time.
""")

# Path to the log file
log_file_path = "app.log"

# Check if the log file exists
if not os.path.exists(log_file_path):
    st.error("Log file 'app.log' not found!")
else:
    # Read the log file
    with open(log_file_path, "r") as f:
        log_contents = f.read()

    # Log Level Filter
    log_levels = ["ALL", "INFO", "ERROR", "DEBUG"]
    selected_log_level = st.selectbox("Choose Log Level", log_levels)

    # Filter logs based on the selected log level
    if selected_log_level != "ALL":
        filtered_logs = [line for line in log_contents.splitlines() if selected_log_level in line]
    else:
        filtered_logs = log_contents.splitlines()

    # Display logs with line number and color-coding based on log level
    log_display = ""
    for line in filtered_logs:
        # Apply color-coding based on log level
        if "ERROR" in line:
            log_display += f'<p style="color:red;">{line}</p>'
        elif "INFO" in line:
            log_display += f'<p style="color:green;">{line}</p>'
        elif "DEBUG" in line:
            log_display += f'<p style="color:blue;">{line}</p>'
        else:
            log_display += f'<p>{line}</p>'

    # Display the formatted logs in the Streamlit app
    st.markdown(log_display, unsafe_allow_html=True)
