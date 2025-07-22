#!/usr/bin/env python3
"""
Overrides meter entry for (TEID, QFI) with anomalous parameters.
Usage:
    python3 metering_anomaly.py --teid 0x1042 --qfi 5 --cir 0 --pir 999999 --cbs 0 --pbs 0
"""

import argparse
import logging
import sys

sys.path.append("/home/n6saha/bfrt_controller")
from bfrt_controller.controller import Controller

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--teid", required=True, help="TEID in hex (e.g. 0x1042)")
    parser.add_argument("--qfi", required=True, type=int)
    parser.add_argument("--cir", required=True, type=int)
    parser.add_argument("--pir", required=True, type=int)
    parser.add_argument("--cbs", required=True, type=int)
    parser.add_argument("--pbs", required=True, type=int)
    return parser.parse_args()

def main():
    args = parse_args()

    teid = int(args.teid, 16)
    qfi = args.qfi

    logging.info(f"Overriding meter for TEID={hex(teid)}, QFI={qfi}")

    c = Controller()
    c.setup_tables(["Ingress.QoSMeter.meter_table"])
    c.add_annotation("Ingress.QoSMeter.meter_table", "hdr.gtpu.teid", "hex")

    entry = (
        [("hdr.gtpu.teid", teid), ("hdr.gtpu_ext_psc.qfi", qfi)],
        "Ingress.QoSMeter.set_color",
        [
            ("$METER_SPEC_CIR_KBPS", args.cir),
            ("$METER_SPEC_PIR_KBPS", args.pir),
            ("$METER_SPEC_CBS_KBITS", args.cbs),
            ("$METER_SPEC_PBS_KBITS", args.pbs),
        ]
    )

    c.program_table("Ingress.QoSMeter.meter_table", [entry])
    c.tear_down()

if __name__ == "__main__":
    main()
