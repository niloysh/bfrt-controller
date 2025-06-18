"""
Configure QFI-to-Queue mapping in the Tofino pipeline.

This script programs `Ingress.QueueMapper.qfi_to_queue_table` with QFI-to-QID mappings
based on service class assumptions or an externally provided config.

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

DEFAULT_MAPPING = {
    1: 0,  # URLLC
    2: 1,  # Cloud Gaming
    3: 2,  # Video Conferencing
    5: 3,  # Streaming
    # Others fall through to default_action → qid = 4
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
