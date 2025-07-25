from shiny import reactive, render
from shiny.express import ui, input
from shinywidgets import render_plotly
import random
from datetime import datetime
from collections import deque
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from faicons import icon_svg

# --------------------------------------------
# Constants & Reactive State
# --------------------------------------------

UPDATE_INTERVAL_SECS: int = 3
DEQUE_SIZE: int = 5
reactive_value_wrapper = reactive.value(deque(maxlen=DEQUE_SIZE))

# --------------------------------------------
# Reactive Calculation for Live Data
# --------------------------------------------

@reactive.calc()
def reactive_calc_combined():
    reactive.invalidate_later(UPDATE_INTERVAL_SECS)

    temp = round(random.uniform(-18, -16), 1)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = {"temp": temp, "timestamp": timestamp}

    reactive_value_wrapper.get().append(new_entry)
    deque_snapshot = reactive_value_wrapper.get()
    df = pd.DataFrame(deque_snapshot)

    return deque_snapshot, df, new_entry

# --------------------------------------------
# UI Layout
# --------------------------------------------

ui.page_opts(title="PyShiny Express: Live Data Example", fillable=True)

with ui.sidebar(open="open"):
    ui.h2("Antarctic Explorer", class_="text-center")
    ui.p("A demonstration of real-time temperature readings in Antarctica.", class_="text-center")
    ui.hr()
    
    ui.input_numeric("temp_threshold", "Alert Threshold (°C)", value=-17.0, step=0.1)

    ui.hr()
    ui.h6("Links:")
    ui.a("GitHub Source", href="https://github.com/denisecase/cintel-05-cintel", target="_blank")
    ui.a("GitHub App", href="https://denisecase.github.io/cintel-05-cintel/", target="_blank")
    ui.a("PyShiny", href="https://shiny.posit.co/py/", target="_blank")
    ui.a("PyShiny Express", href="https://shiny.posit.co/blog/posts/shiny-express/", target="_blank")

# --------------------------------------------
# Value Box with Color-coded Alert
# --------------------------------------------

@reactive.calc()
def alert_theme():
    _, _, latest = reactive_calc_combined()
    threshold = input.temp_threshold()
    return "bg-gradient-red" if latest["temp"] > threshold else "bg-gradient-blue-purple"

with ui.layout_columns():
    with ui.value_box(showcase=icon_svg("sun"), theme="purple"):  # use static theme
        "Current Temperature"

        @render.text
        def display_temp():
            _, _, latest = reactive_calc_combined()
            return f"{latest['temp']} °C"

        @render.text
        def temp_status():
            _, _, latest = reactive_calc_combined()
            threshold = input.temp_threshold()
            return (
                "🔴 ⚠️ Above Threshold!" if latest["temp"] > threshold else "🟢 ✅ Normal Range"
            )

# --------------------------------------------
# Cards
# --------------------------------------------

with ui.card(full_screen=True):
    ui.card_header("Current Date and Time")

    @render.text
    def display_time():
        _, _, latest = reactive_calc_combined()
        return latest["timestamp"]

with ui.card(full_screen=True):
    ui.card_header("Most Recent Readings")

    @render.data_frame
    def display_df():
        _, df, _ = reactive_calc_combined()
        return render.DataGrid(df, width="100%")

with ui.card():
    ui.card_header("Chart with Current Trend and Alert Line")

    @render_plotly
    def display_plot():
        _, df, _ = reactive_calc_combined()
        if df.empty:
            return px.scatter()

        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Scatter plot
        fig = px.scatter(
            df,
            x="timestamp",
            y="temp",
            title="Temperature Readings with Regression Line",
            labels={"temp": "Temperature (°C)", "timestamp": "Time"},
            color_discrete_sequence=["blue"],
        )

        # Add regression line
        x_vals = list(range(len(df)))
        y_vals = df["temp"]
        slope, intercept, *_ = stats.linregress(x_vals, y_vals)
        df["best_fit_line"] = [slope * x + intercept for x in x_vals]

        fig.add_scatter(
            x=df["timestamp"],
            y=df["best_fit_line"],
            mode="lines",
            name="Regression Line",
            line=dict(color="purple")
        )

        # Add horizontal threshold line
        threshold = input.temp_threshold()
        fig.add_trace(
            go.Scatter(
                x=[df["timestamp"].min(), df["timestamp"].max()],
                y=[threshold, threshold],
                mode="lines",
                name="Threshold",
                line=dict(color="red", dash="dash")
            )
        )

        fig.update_layout(xaxis_title="Time", yaxis_title="Temperature (°C)")
        return fig
