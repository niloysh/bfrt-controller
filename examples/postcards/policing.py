"""
Configure policing for meter colors.
YELLOW goes to best-effort queue i.e., qid 7
RED is dropped.

Usage:
    python3 metering.py
"""

import logging
import sys

sys.path.append("/home/n6saha/bfrt_controller")
from bfrt_controller.controller import Controller

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    c = Controller()
    c.setup_tables(["Ingress.QoSMeter.qos_table"])

    entries = [
        ([("meta.bridged_md.meter_color", 0)], "Ingress.QoSMeter.count_drop", []),
        ([("meta.bridged_md.meter_color", 1)], "Ingress.QoSMeter.set_queue", [("qid", 7)]),
        ([("meta.bridged_md.meter_color", 2)], "Ingress.QoSMeter.set_queue", [("qid", 7)]),
        ([("meta.bridged_md.meter_color", 3)], "Ingress.QoSMeter.drop", []),
        
    ]

    logging.info(f"Installing entries for qos_table")
    c.program_table("Ingress.QoSMeter.qos_table", entries)
    c.tear_down()


if __name__ == "__main__":
    main()
