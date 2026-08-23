import os

# ---- Paths ----
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
FIGURES_DIR = os.path.join(OUTPUT_DIR, "figures")
MODELS_DIR = os.path.join(OUTPUT_DIR, "models")

TRAIN_PATH = os.path.join(DATA_DIR, "KDDTrain.csv")
TEST_PATH = os.path.join(DATA_DIR, "KDDTest.csv")

TRAIN_URL = (
    "https://raw.githubusercontent.com/Mamcose/"
    "NSL-KDD-Network-Intrusion-Detection/master/NSL_KDD_Train.csv"
)
TEST_URL = (
    "https://raw.githubusercontent.com/Mamcose/"
    "NSL-KDD-Network-Intrusion-Detection/master/NSL_KDD_Test.csv"
)

# ---- Dataset schema ----
COLUMN_NAMES = [
    "duration", "protocol_type", "service", "flag", "src_bytes",
    "dst_bytes", "land", "wrong_fragment", "urgent", "hot",
    "num_failed_logins", "logged_in", "num_compromised", "root_shell",
    "su_attempted", "num_root", "num_file_creations", "num_shells",
    "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
    "dst_host_srv_count", "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate",
    "dst_host_srv_serror_rate", "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate", "label",
]

CATEGORICAL_COLS = ["protocol_type", "service", "flag"]

ATTACK_MAPPING = {
    "neptune": "DoS", "back": "DoS", "land": "DoS", "pod": "DoS",
    "smurf": "DoS", "teardrop": "DoS", "mailbomb": "DoS",
    "processtable": "DoS", "udpstorm": "DoS", "apache2": "DoS", "worm": "DoS",
    "satan": "Probe", "ipsweep": "Probe", "nmap": "Probe",
    "portsweep": "Probe", "mscan": "Probe", "saint": "Probe",
    "guess_passwd": "R2L", "ftp_write": "R2L", "imap": "R2L",
    "phf": "R2L", "multihop": "R2L", "warezmaster": "R2L",
    "warezclient": "R2L", "spy": "R2L", "xlock": "R2L",
    "xsnoop": "R2L", "snmpguess": "R2L", "snmpgetattack": "R2L",
    "httptunnel": "R2L", "sendmail": "R2L", "named": "R2L",
    "buffer_overflow": "U2R", "loadmodule": "U2R", "rootkit": "U2R",
    "perl": "U2R", "sqlattack": "U2R", "xterm": "U2R", "ps": "U2R",
    "normal": "normal",
}

# ---- Final locked hyperparameters ----
PCA_N_COMPONENTS = 20
DBSCAN_EPS = 0.8
DBSCAN_MIN_SAMPLES = 5

TRAIN_SAMPLE_SIZE = 35000
RANDOM_SEED = 42

if __name__ == "__main__":
    print(BASE_DIR)
    print(DATA_DIR)
