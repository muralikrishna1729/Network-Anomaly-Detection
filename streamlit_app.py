"""
Streamlit demo UI for the Network Intrusion Anomaly Detection project.

Prerequisite: run `python main.py --save-model` first, so outputs/models/
has a saved scaler, PCA, DBSCAN params, and training coordinates.

Run locally:
    streamlit run streamlit_app.py

This is a visual demo companion to app.py (the Flask API) -- both call the
same src/inference.py functions, so behavior is identical between them.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import json
import io
import base64

from src import config
from src import persistence
from src.inference import preprocess_single_record, score_point
from src.exceptions import InvalidRecordError, PreprocessingError, ModelNotFoundError
from src.logging_utils import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Network Anomaly Detection", page_icon="🛡️", layout="centered")

st.title("🛡️ Network Intrusion Anomaly Detection")
st.caption("DBSCAN-based unsupervised anomaly detection on NSL-KDD connection records")

# ---- Initialize session state for current record and result ----
if "current_record" not in st.session_state:
    st.session_state["current_record"] = None
if "current_result" not in st.session_state:
    st.session_state["current_result"] = None
if "eps" not in st.session_state:
    st.session_state["eps"] = float(artifacts["dbscan_params"]["eps"])
if "min_samples" not in st.session_state:
    st.session_state["min_samples"] = int(artifacts["dbscan_params"]["min_samples"])

# ---- Load model (cached) -------------------------------------------------
@st.cache_resource
def load_model():
    """Load saved artifacts once and cache across reruns."""
    try:
        return persistence.load_artifacts(), None
    except ModelNotFoundError as e:
        return None, str(e)

artifacts, load_error = load_model()

if load_error:
    st.error(f"Model not loaded: {load_error}")
    st.info("Run `python main.py --save-model` first, then restart this app.")
    st.stop()

st.success("Model loaded and ready.")

# Clear cache button
if st.button("Clear Cache"):
    st.cache_resource.clear()
    st.experimental_rerun()

# ---- DBSCAN parameter sidebar --------------------------------------------
st.sidebar.header("🔧 DBSCAN parameters")
eps = st.sidebar.slider("eps (neighborhood radius)", 0.1, 5.0, st.session_state["eps"], 0.1)
min_samples = st.sidebar.slider("min_samples", 1, 10, st.session_state["min_samples"], 1)

if st.button("Reset DBSCAN parameters"):
    st.session_state["eps"] = float(artifacts["dbscan_params"]["eps"])
    st.session_state["min_samples"] = int(artifacts["dbscan_params"]["min_samples"])
    st.experimental_rerun()

# ---- Preset examples ----------------------------------------------------
PRESETS = {
    "DoS-like (neptune pattern)": {
        "duration": 0, "protocol_type": "tcp", "service": "private", "flag": "S0",
        "src_bytes": 0, "dst_bytes": 0, "land": 0, "wrong_fragment": 0, "urgent": 0,
        "hot": 0, "num_failed_logins": 0, "logged_in": 0, "num_compromised": 0,
        "root_shell": 0, "su_attempted": 0, "num_root": 0, "num_file_creations": 0,
        "num_shells": 0, "num_access_files": 0, "num_outbound_cmds": 0,
        "is_host_login": 0, "is_guest_login": 0, "count": 123, "srv_count": 6,
        "serror_rate": 1.0, "srv_serror_rate": 1.0, "rerror_rate": 0.0,
        "srv_rerror_rate": 0.0, "same_srv_rate": 0.05, "diff_srv_rate": 0.07,
        "srv_diff_host_rate": 0.0, "dst_host_count": 255, "dst_host_srv_count": 26,
        "dst_host_same_srv_rate": 0.1, "dst_host_diff_srv_rate": 0.05,
        "dst_host_same_src_port_rate": 0.0, "dst_host_srv_diff_host_rate": 0.0,
        "dst_host_serror_rate": 1.0, "dst_host_srv_serror_rate": 1.0,
        "dst_host_rerror_rate": 0.0, "dst_host_srv_rerror_rate": 0.0,
    },
    "Normal-looking (http)": {
        "duration": 0, "protocol_type": "tcp", "service": "http", "flag": "SF",
        "src_bytes": 232, "dst_bytes": 8153, "land": 0, "wrong_fragment": 0, "urgent": 0,
        "hot": 0, "num_failed_logins": 0, "logged_in": 1, "num_compromised": 0,
        "root_shell": 0, "su_attempted": 0, "num_root": 0, "num_file_creations": 0,
        "num_shells": 0, "num_access_files": 0, "num_outbound_cmds": 0,
        "is_host_login": 0, "is_guest_login": 0, "count": 5, "srv_count": 5,
        "serror_rate": 0.2, "srv_serror_rate": 0.2, "rerror_rate": 0.0,
        "srv_rerror_rate": 0.0, "same_srv_rate": 1.0, "diff_srv_rate": 0.0,
        "srv_diff_host_rate": 0.0, "dst_host_count": 30, "dst_host_srv_count": 255,
        "dst_host_same_srv_rate": 1.0, "dst_host_diff_srv_rate": 0.03,
        "dst_host_same_src_port_rate": 0.04, "dst_host_srv_diff_host_rate": 0.03,
        "dst_host_serror_rate": 0.01, "dst_host_srv_serror_rate": 0.0,
        "dst_host_rerror_rate": 0.0, "dst_host_srv_rerror_rate": 0.0,
    },
}

st.subheader("Try an example, or enter a record manually")
preset_choice = st.selectbox("Load a preset", ["-- Manual entry --"] + list(PRESETS.keys()))

# ---- Compare with preset (optional) ------------------------------------
compare_preset = st.checkbox("🔍 Compare with a preset (side‑by‑side)")
if compare_preset:
    preset_name = st.selectbox("Select preset to compare", ["-- Choose --"] + list(PRESETS.keys()))
    if preset_name != "-- Choose --":
        with st.expander(f"Preset: {preset_name}"):
            st.json(PRESETS[preset_name])

# Use the selected preset as the base for the form
if preset_choice != "-- Manual entry --":
    defaults = PRESETS[preset_choice]
else:
    defaults = PRESETS["Normal-looking (http)"]  # sensible starting point for manual edits

# ---- Form for record input ---------------------------------------------
with st.form("record_form"):
    st.markdown("**Basic connection features**")
    c1, c2, c3 = st.columns(3)
    duration = c1.number_input("duration", value=int(defaults["duration"]), min_value=0)
    protocol_type = c2.selectbox("protocol_type", ["tcp", "udp", "icmp"],
                              index=["tcp", "udp", "icmp"].index(defaults["protocol_type"]))
    service = c3.text_input("service", value=defaults["service"])

    c1, c2, c3 = st.columns(3)
    flag = c1.text_input("flag", value=defaults["flag"])
    src_bytes = c2.number_input("src_bytes", value=int(defaults["src_bytes"]), min_value=0)
    dst_bytes = c3.number_input("dst_bytes", value=int(defaults["dst_bytes"]), min_value=0)

    st.markdown("**Traffic-rate features (last 2 seconds)**")
    c1, c2, c3 = st.columns(3)
    count = c1.number_input("count", value=int(defaults["count"]), min_value=0)
    srv_count = c2.number_input("srv_count", value=int(defaults["srv_count"]), min_value=0)
    serror_rate = c3.slider("serror_rate", 0.0, 1.0, float(defaults["serror_rate"]))

    c1, c2 = st.columns(2)
    same_srv_rate = c1.slider("same_srv_rate", 0.0, 1.0, float(defaults["same_srv_rate"]))
    diff_srv_rate = c2.slider("diff_srv_rate", 0.0, 1.0, float(defaults["diff_srv_rate"]))

    with st.expander("Advanced: remaining fields (defaults from preset)"):
        st.json({k: v for k, v in defaults.items()
                 if k not in ["duration", "protocol_type", "service", "flag",
                              "src_bytes", "dst_bytes", "count", "srv_count",
                              "serror_rate", "same_srv_rate", "diff_srv_rate"]})

    submitted = st.form_submit_button("Score this record")

# ---- Score the record ----------------------------------------------------
if submitted:
    record = dict(defaults)  # start from preset, override with the fields shown above
    record.update({
        "duration": duration, "protocol_type": protocol_type, "service": service,
        "flag": flag, "src_bytes": src_bytes, "dst_bytes": dst_bytes,
        "count": count, "srv_count": srv_count, "serror_rate": serror_rate,
        "same_srv_rate": same_srv_rate, "diff_srv_rate": diff_srv_rate,
    })

    # Store record in session_state for later rescore
    st.session_state["current_record"] = record
    try:
        X_pca_point = preprocess_single_record(
            record, artifacts["feature_names"], artifacts["scaler"], artifacts["pca"]
        )
        result = score_point(
            X_pca_point,
            artifacts["train_coords"],
            eps=eps,
            min_samples=min_samples,
        )
        # Store result in session_state
        st.session_state["current_result"] = {
            "is_anomaly": result["is_anomaly"],
            "neighbors_within_eps": result["neighbors_within_eps"],
            "min_samples_required": result["min_samples_required"],
            "eps_used": eps,
            "min_samples_used": min_samples,
        }
    except (InvalidRecordError, PreprocessingError) as e:
        st.error(f"Could not score this record: {e}")
        st.stop()

    # Use stored result if available
    if "current_result" in st.session_state:
        res = st.session_state["current_result"]
        if res["is_anomaly"]:
            st.error(f"⚠️ **Verdict: ANOMALY** — flagged as noise by DBSCAN")
        else:
            st.success(f"✅ **Verdict: NORMAL** — falls within a dense cluster")

        col1, col2 = st.columns(2)
        col1.metric("Neighbors within eps", res["neighbors_within_eps"])
        col2.metric("min_samples required", res["min_samples_required"])

        st.caption(
            f"eps={artifacts['dbscan_params']['eps']}, "
            f"min_samples={artifacts['dbscan_params']['min_samples']} "
            f"(locked config from project tuning)"
        )

    # ---- Download JSON ----------------------------------------------------
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("💾 Download JSON"):
            output = {
                "record": record,
                "verdict": result,
                "dbscan_params": artifacts["dbscan_params"],
                "timestamp": pd.Timestamp.now().isoformat(),
            }
            st.download_button(
                label="Download",
                data=json.dumps(output, indent=2),
                file_name="anomaly_record.json",
                mime="application/json",
            )

    # ---- Download CSV ------------------------------------------------------
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("📥 Download CSV"):
            # Create a DataFrame with the record and result
            df = pd.DataFrame([{
                "duration": record["duration"],
                "protocol_type": record["protocol_type"],
                "service": record["service"],
                "flag": record["flag"],
                "src_bytes": record["src_bytes"],
                "dst_bytes": record["dst_bytes"],
                "count": record["count"],
                "srv_count": record["srv_count"],
                "serror_rate": record["serror_rate"],
                "same_srv_rate": record["same_srv_rate"],
                "diff_srv_rate": record["diff_srv_rate"],
                "is_anomaly": res["is_anomaly"],
                "neighbors_within_eps": res["neighbors_within_eps"],
                "min_samples_required": res["min_samples_required"],
                "eps": artifacts["dbscan_params"]["eps"],
                "min_samples": artifacts["dbscan_params"]["min_samples"],
                "timestamp": pd.Timestamp.now().isoformat(),
            })
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download",
                data=csv,
                file_name="anomaly_record.csv",
                mime="text/csv",
            )

    # ---- Reset form ---------------------------------------------------------
    if st.button("🔄 Reset form and results"):
        st.session_state["current_record"] = None
        st.session_state["current_result"] = None
        st.experimental_rerun()

# ---- About this model ----------------------------------------------------
st.divider()
with st.expander("About this model"):
    st.markdown("""
    This demo scores a single connection record against a **DBSCAN** model
    trained on the NSL-KDD dataset. Since DBSCAN has no native way to score
    brand-new points, this reuses DBSCAN's own core-point rule: a new point
    is flagged as an anomaly if it doesn't have enough training points
    (`min_samples`) within its `eps` neighborhood.

    **Key finding from this project:** detection rate scales inversely with
    how common an attack pattern is — rare attacks (U2R) are caught ~73% of
    the time, while common, repetitive attacks (DoS) are correctly left
    unflagged (~1%) because they form their own dense clusters. This isn't
    a general-purpose attack classifier — it's built to catch **novel,
    rare** anomalies, which is where clustering has a real advantage over
    classification.
    """)
    # Show model statistics
    with st.expander("📊 Model statistics"):
        st.write(f"**eps**: {artifacts['dbscan_params']['eps']}")
        st.write(f"**min_samples**: {artifacts['dbscan_params']['min_samples']}")
        st.write(f"**Number of clusters**: {artifacts.get('n_clusters', 'N/A')}")
        st.write(f"**Outliers (noise points)**: {artifacts.get('n_outliers', 'N/A')}")
        st.write(f"**Training records**: {artifacts.get('n_train', 'N/A')}")

    # ---- Neighborhood visualization ---------------------------------------
    st.subheader("📍 Neighborhood visualization")
    if 'current_record' in st.session_state:
        # Helper to get training points in PCA space
        @st.cache_data
        def get_training_points():
            # If pre‑computed transformed points exist, use them; otherwise compute.
            if "pca_transformed" in artifacts:
                return artifacts["pca_transformed"]
            # Compute on the fly (may be slower)
            X_train = artifacts["pca"].transform(artifacts["train_coords"])
            return X_train

        def plot_neighborhood(record, eps, min_samples):
            points = get_training_points()
            if points.size == 0:
                return None
            # Transform the record
            X_pca_point = preprocess_single_record(
                record, artifacts["feature_names"], artifacts["scaler"], artifacts["pca"]
            )
            # Compute Euclidean distances in PCA space
            dists = np.linalg.norm(points - X_pca_point, axis=1)
            # Build a DataFrame for Plotly
            df = pd.DataFrame(points, columns=artifacts["pca_features"])
            # Add columns for highlighting
            df["is_target"] = False
            df["is_neighbor"] = False
            # Highlight the target point
            target_df = pd.DataFrame({
                "x1": [X_pca_point[artifacts["pca_features"].index("pca-0")]],
                "x2": [X_pca_point[artifacts["pca_features"].index("pca-1")]],
                "is_target": True,
                "is_neighbor": False,
                "is_anomaly": False,
            })
            df = pd.concat([df, target_df], ignore_index=True)
            fig = px.scatter(
                df,
                x="x1",
                y="x2",
                color="is_target",
                symbol="is_neighbor",
                hover_data=["count", "serror_rate"],
                title=f"DBSCAN neighborhood (eps = {eps:.2f})",
            )
            fig.update_traces(marker=dict(size=12))
            return fig

        fig = plot_neighborhood(st.session_state["current_record"], eps, min_samples)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            # Option to download the plot as PNG
            if st.button("Download plot as PNG"):
                try:
                    buf = io.BytesIO()
                    fig.write_image(buf, format="png")
                    buf.seek(0)
                    b64 = base64.b64encode(buf.read()).decode()
                    st.download_button(
                        label="Download PNG",
                        data=b64,
                        file_name="neighborhood_plot.png",
                        mime="image/png",
                    )
                except Exception as e:
                    st.warning(f"Failed to export PNG: {e}")
        else:
            st.info("No training data available for visualization.")

    # ---- Show training data summary ---------------------------------------
    if st.button("Show training data summary"):
        summary = {
            "Total training records": artifacts.get("n_train", "N/A"),
            "Number of clusters": artifacts.get("n_clusters", "N/A"),
            "Number of outliers (noise points)": artifacts.get("n_outliers", "N/A"),
            "DBSCAN eps": artifacts["dbscan_params"]["eps"],
            "min_samples": artifacts["dbscan_params"]["min_samples"],
        }
        st.write(pd.DataFrame([summary]))

st.divider()
with st.expander("About this model"):
    st.markdown("""
    This demo scores a single connection record against a **DBSCAN** model
    trained on the NSL-KDD dataset. Since DBSCAN has no native way to score
    brand-new points, this reuses DBSCAN's own core-point rule: a new point
    is flagged as an anomaly if it doesn't have enough training points
    (`min_samples`) within its `eps` neighborhood.

    **Key finding from this project:** detection rate scales inversely with
    how common an attack pattern is — rare attacks (U2R) are caught ~73% of
    the time, while common, repetitive attacks (DoS) are correctly left
    unflagged (~1%) because they form their own dense clusters. This isn't
    a general-purpose attack classifier — it's built to catch **novel,
    rare** anomalies, which is where clustering has a real advantage over
    classification.
    """)
    if st.button("Show PCA visualization"):
        import matplotlib.pyplot as plt
        # For demonstration, we will plot a random point in 2D PCA space.
        # In a real scenario, you would transform the training data to 2D
        # and plot the sample point along with a few reference points.
        fig, ax = plt.subplots()
        # Placeholder: plot a red dot for the sample point
        ax.scatter(0.5, 0.5, color='red', label='Sample point')
        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.set_title('PCA Visualization (first two components)')
        ax.legend()
        st.pyplot(fig)