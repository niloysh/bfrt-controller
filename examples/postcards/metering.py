"""
Configure RFC 2697 trTCM meters for each (TEID, QFI) pair on Tofino.

Usage:
    python3 metering.py
"""

import logging
import sys

sys.path.append("/home/n6saha/bfrt_controller")
from bfrt_controller.controller import Controller

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Token bucket parameters per QFI (CIR, PIR in kbps; CBS, PBS in kbits)
QFI_METER_PARAMS = {
    1: {  # URLLC (QID0)
        "CIR_KBPS": 20_000,
        "PIR_KBPS": 100_000,      
        "CBS_KBITS": 120,        
        "PBS_KBITS": 360         
    },
    5: {  # IoT (QID1)
        "CIR_KBPS": 20_000,
        "PIR_KBPS": 100_000,     
        "CBS_KBITS": 480,   
        "PBS_KBITS": 1440,   
    },
    3: {  # Gaming (QID2)
        "CIR_KBPS": 70_000,
        "PIR_KBPS": 800_000, 
        "CBS_KBITS": 480,  
        "PBS_KBITS": 1500 
    },
    7: {  # Video call (QID3)
        "CIR_KBPS": 50_000,
        "PIR_KBPS": 100_000,
        "CBS_KBITS": 180,  
        "PBS_KBITS": 540,
    },
    4: {  # YouTube (QID4)
        "CIR_KBPS": 250_000,
        "PIR_KBPS": 450_000,
        "CBS_KBITS": 700, 
        "PBS_KBITS": 1_440
    },
    2: {  # Twitch (QID5)
        "CIR_KBPS": 150_000,
        "PIR_KBPS": 350_000,
        "CBS_KBITS": 850,
        "PBS_KBITS": 2160,
    },
    6: {  # Downloads (QID6)
        "CIR_KBPS": 100_000,   
        "PIR_KBPS": 500_000,   
        "CBS_KBITS": 960,     
        "PBS_KBITS": 2_880     
    },
    8: {  # File sync (QID7)
        "CIR_KBPS": 450_000,  
        "PIR_KBPS": 800_000,
        "CBS_KBITS": 1500,
        "PBS_KBITS": 2500
    },
    9: {  # Browsing (QID7)
        "CIR_KBPS": 80_000,
        "PIR_KBPS": 220_000,
        "CBS_KBITS": 600,
        "PBS_KBITS": 1800
    },
}

BASE_TEID = 0x0001  # Start TEID
UE_COUNT = 110
QFIS = sorted(QFI_METER_PARAMS.keys())


def main():
    c = Controller()
    c.setup_tables(["Ingress.QoSMeter.meter_table"])
    c.add_annotation("Ingress.QoSMeter.meter_table", "hdr.gtpu.teid", "hex")

    entries = []

    for ue in range(UE_COUNT):
        teid = BASE_TEID + ue
        for qfi in QFIS:
            params = QFI_METER_PARAMS[qfi]
            entry = (
                [("hdr.gtpu.teid", teid), ("hdr.gtpu_ext_psc.qfi", qfi)],
                "Ingress.QoSMeter.set_color",
                [
                    ("$METER_SPEC_CIR_KBPS", params["CIR_KBPS"]),
                    ("$METER_SPEC_PIR_KBPS", params["PIR_KBPS"]),
                    ("$METER_SPEC_CBS_KBITS", params["CBS_KBITS"]),
                    ("$METER_SPEC_PBS_KBITS", params["PBS_KBITS"]),
                ]
            )
            entries.append(entry)

    logging.info(f"Installing {len(entries)} meter entries for {UE_COUNT} UEs × {len(QFIS)} QFIs")
    c.program_table("Ingress.QoSMeter.meter_table", entries)
    c.tear_down()


if __name__ == "__main__":
    main()
