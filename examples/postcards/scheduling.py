#!/usr/bin/env python3

"""
Applies 5G-style queue scheduling policies on Tofino egress queues using BFRT gRPC.

Run: python3 scheduling_grpc.py
"""

import sys
import json
sys.path.append("/home/n6saha/bfrt_controller")

import os
import logging
from bfrt_controller import Controller
from bfrt_controller.bfrt_grpc import client as gc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Device ports to configure
DEV_PORTS = [16]

# QID → Scheduling configuration for 1000 TEIDs
# Based on report from traffic generator (See https://github.com/niloysh/5g-traffic-generator)
# QFI 1: 101.06 Mbps
# QFI 2: 762.95 Mbps
# QFI 3: 249.15 Mbps
# QFI 5: 2347.47 Mbps
# QFI 9: 1135.07 Mbps

# Total cap: 0.3 + 1 + 0.5 + 3 + 1.5 = 6.3

# Load QID_CFG from JSON if CONFIG_FILE is set
if os.getenv("CONFIG_FILE") and os.path.isfile(os.getenv("CONFIG_FILE")):
    with open(os.getenv("CONFIG_FILE")) as f:
        QID_CFG = {int(k): v for k, v in json.load(f).items()}
    logging.info(f"Loaded QID_CFG from {os.getenv('CONFIG_FILE')}")
else:
    logging.info("Using hardcoded QID_CFG")
    QID_CFG = {
        # QFI 1 - real-time gaming (e.g, Battlegrounds)
        0: {
            "max_priority": 7,  # highest priority
            "min_rate": 800000,  # 800 Mbps guaranteed
            "max_rate": None  # No cap
        },
        # QFI 2 - Cloud gaming
        1: {
            "max_priority": 5, # 2nd highest priority
            "min_rate": 2000000,  # 2Gbps guaranteed (720p/1080p streams)
            "max_rate": 7000000  # 7Gbps cap
        },    
        # QFI 3 - Video conferencing
        2: {
            "max_priority": 3, # mid priority
            "min_rate": 750000,  # No guarantee  1 Gbps 
            "max_rate": 4000000  # 4 Gbps cap
        },
        # QFI 5 - Streaming
        3: {
            "max_priority": 2, # low priority
            "min_rate": None,  # No guarantees
            "max_rate": 6000000  # 6 Gbps cap (e.g., 4K streams)
        }, 
        # QFI 9 - Best effort
        4: {
            "max_priority": 1,  # lowest priority
            "min_rate": None,    # No guarantee
            "max_rate": 5000000   # 5 Gbps cap
            },
    }



def apply_sched_policy(controller, dev_port, qid_cfg):
    pipe = dev_port >> 7

    port_cfg_table = controller.bfrt_info.table_get("tf1.tm.port.cfg")
    port_key = port_cfg_table.make_key([gc.KeyTuple("dev_port", dev_port)])
    data, _ = next(port_cfg_table.entry_get(controller.target, [port_key], {"from_hw": True}))
    pg_id = data.to_dict()["pg_id"]
    qid_map = data.to_dict()["egress_qid_queues"]

    logging.info(f"Configuring DEV_PORT {dev_port} → Pipe {pipe}, PG_ID {pg_id}")

    sched_cfg = controller.bfrt_info.table_get("tf1.tm.queue.sched_cfg")
    sched_shaping = controller.bfrt_info.table_get("tf1.tm.queue.sched_shaping")

    cfg_keys, cfg_data = [], []
    shaping_keys, shaping_data = [], []

    for logical_qid, cfg in qid_cfg.items():
        physical_qid = qid_map[logical_qid]
        logging.info(f"→ QID {logical_qid} (PG_QUEUE {physical_qid}) → Priority {cfg['max_priority']}")

        # --- SCHED_CFG ---
        cfg_keys.append(sched_cfg.make_key([
            gc.KeyTuple("pg_id", pg_id),
            gc.KeyTuple("pg_queue", physical_qid),
        ]))
        cfg_data.append(sched_cfg.make_data([
            gc.DataTuple("max_priority", str_val=str(cfg["max_priority"])),
            gc.DataTuple("max_rate_enable", bool_val=cfg["max_rate"] is not None),
            gc.DataTuple("min_rate_enable", bool_val=cfg["min_rate"] is not None),
            gc.DataTuple("scheduling_enable", bool_val=True),
        ]))

        # --- SCHED_SHAPING ---
        shaping_keys.append(sched_shaping.make_key([
            gc.KeyTuple("pg_id", pg_id),
            gc.KeyTuple("pg_queue", physical_qid),
        ]))
        shaping_data.append(sched_shaping.make_data([
            gc.DataTuple("unit", str_val="BPS"),
            gc.DataTuple("provisioning", str_val="UPPER"),
            gc.DataTuple("max_rate", cfg["max_rate"] or 0),
            gc.DataTuple("min_rate", cfg["min_rate"] or 0),
            gc.DataTuple("max_burst_size", 0),
            gc.DataTuple("min_burst_size", 0),
        ]))

    # Perform batched updates
    sched_cfg.entry_mod(controller.target, cfg_keys, cfg_data)
    sched_shaping.entry_mod(controller.target, shaping_keys, shaping_data)

def main():
    c = Controller(pipe_id=0x0000)
    c.setup_tables(["tf1.tm.port.cfg", "tf1.tm.queue.sched_cfg", "tf1.tm.queue.sched_shaping"])

    logging.info("Applying Queue Scheduling Policy via gRPC")
    for dev_port in DEV_PORTS:
        apply_sched_policy(c, dev_port, QID_CFG)

    c.tear_down()

if __name__ == "__main__":
    main()
