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
    9: {  # browsing.pcap
        "CIR_KBPS": 5658,
        "PIR_KBPS": 45448,
        "CBS_KBITS": 737701 * 8 // 1000,  # ≈ 5901
        "PBS_KBITS": 1106551 * 8 // 1000  # ≈ 8852
    },
    6: {  # file-download-http.pcap
        "CIR_KBPS": 472836,
        "PIR_KBPS": 825913,
        "CBS_KBITS": 11493378 * 8 // 1000,  # ≈ 91947
        "PBS_KBITS": 17240067 * 8 // 1000  # ≈ 137920
    },
    8: {  # file-sync-nextcloud.pcap
        "CIR_KBPS": 83315,
        "PIR_KBPS": 829756,
        "CBS_KBITS": 12472141 * 8 // 1000,  # ≈ 99777
        "PBS_KBITS": 18708211 * 8 // 1000  # ≈ 149665
    },
    3: {  # geforce_skyrim.pcap
        "CIR_KBPS": 28776,
        "PIR_KBPS": 35428,
        "CBS_KBITS": 556880 * 8 // 1000,  # ≈ 4455
        "PBS_KBITS": 835320 * 8 // 1000   # ≈ 6682
    },
    # 5: {  # flame_sensor.pcap
    #     "CIR_KBPS": 350,
    #     "PIR_KBPS": 656,
    #     "CBS_KBITS": 11070 * 8 // 1000,  # ≈ 3
    #     "PBS_KBITS": 652 * 8 // 1000   # ≈ 5
    # },
    5: {  # flame_sensor.pcap
        "CIR_KBPS": 350,     # Keep average rate
        "PIR_KBPS": 1000,    # Allow more room for short bursts
        "CBS_KBITS": 160,    # 20 KB token bucket (up from ~88 KB)
        "PBS_KBITS": 256     # 32 KB peak bucket (up from ~132 KB)
    },
    7: {  # teams.pcap
        "CIR_KBPS": 2489,
        "PIR_KBPS": 7253,
        "CBS_KBITS": 197648 * 8 // 1000,  # ≈ 1581
        "PBS_KBITS": 296472 * 8 // 1000   # ≈ 2371
    },
    2: {  # twitch.pcap
        "CIR_KBPS": 6049,
        "PIR_KBPS": 9057,
        "CBS_KBITS": 333823 * 8 // 1000,  # ≈ 2670
        "PBS_KBITS": 500734 * 8 // 1000   # ≈ 4005
    },
    1: {  # voip.pcap
        "CIR_KBPS": 375,
        "PIR_KBPS": 48018,
        "CBS_KBITS": 5661267 * 8 // 1000,  # ≈ 45290
        "PBS_KBITS": 8491900 * 8 // 1000   # ≈ 67935
    },
    4: {  # youtube.pcap
        "CIR_KBPS": 1861,
        "PIR_KBPS": 47602,
        "CBS_KBITS": 5047277 * 8 // 1000,  # ≈ 40378
        "PBS_KBITS": 7570915 * 8 // 1000   # ≈ 60567
    }
}

BASE_TEID = 0x1000  # Start TEID
UE_COUNT = 100
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
