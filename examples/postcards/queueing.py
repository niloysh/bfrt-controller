"""
Configure QFI-to-Queue mapping in the Tofino pipeline.

This script programs `Ingress.QueueMapper.qfi_to_queue_table` with QFI-to-QID mappings
based on application classes or an external config.

Usage:
    # Use default mapping
    python3 queueing.py

    # Use external config
    CONFIG_FILE=/tmp/queueing_config.json python3 queueing.py
"""

import os
import json
import sys
import logging

sys.path.append("/home/n6saha/bfrt_controller")
from bfrt_controller import Controller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Default QFI → QID mapping for Tofino 8-queue scheduler
# Queue 7 is reserved for best-effort (browsing, sync)
DEFAULT_MAPPING = {
    1: 0,  # VoIP (5QI 1) – URLLC-style, ultra-low latency
    5: 1,  # IoT/MQTT (5QI 75) – low latency telemetry
    3: 2,  # Cloud gaming (5QI 3) – interactive real-time
    7: 3,  # Video call (5QI 65) – less sensitive than VoIP
    4: 4,  # YouTube (5QI 2) – buffered video
    2: 5,  # Twitch (5QI 2) – live stream
    6: 6,  # File download (5QI 6) – throughput heavy
    9: 7,  # Browsing (5QI 9) – best-effort
    8: 7,  # File sync (5QI 6) – background sync (best-effort)
}


def load_mapping():
    path = os.getenv("CONFIG_FILE")
    if path and os.path.exists(path):
        logging.info(f"Loading QFI→QID mapping from {path}")
        with open(path) as f:
            return {int(k): v for k, v in json.load(f).items()}
    else:
        logging.info("Using default QFI→QID mapping")
        return DEFAULT_MAPPING


def program_qfi_to_queue(c: Controller, qfi_to_qid: dict):
    """Install QFI-to-queue mappings into qfi_to_queue_table."""
    logging.info("Programming qfi_to_queue_table")
    c.add_annotation("Ingress.QueueMapper.qfi_to_queue_table", "hdr.gtpu_ext_psc.qfi", "int")

    entries = [
        ([("hdr.gtpu_ext_psc.qfi", qfi)], "Ingress.QueueMapper.set_queue", [("qid", qid)])
        for qfi, qid in qfi_to_qid.items()
    ]

    c.program_table("Ingress.QueueMapper.qfi_to_queue_table", entries)


def main():
    c = Controller()
    c.setup_tables([
        "Ingress.QueueMapper.qfi_to_queue_table"
    ])

    qfi_to_qid = load_mapping()
    program_qfi_to_queue(c, qfi_to_qid)

    c.tear_down()


if __name__ == "__main__":
    main()
