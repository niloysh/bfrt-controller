import os
import sys
import pandas as pd
import argparse
import logging

sys.path.append("/home/n6saha/bfrt_controller")

from bfrt_controller import Controller
from bfrt_controller.bfrt_grpc import client as gc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def dump_register_df(c, reg_name: str, csv_path: str = None, top_k: int = 10, pipe: int = 0):
    """Reads a register in batched mode, optionally writes non-zero entries to CSV, and prints summary stats."""
    if not c.table_exists(reg_name):
        print(f"[WARN] Register '{reg_name}' does not exist.")
        return

    print(f"[INFO] Reading register: {reg_name}")
    reg_values = c.read_register_batched(reg_name, pipe=pipe)
    df = pd.DataFrame(reg_values, columns=["index", "value"])

    # Filter non-zero
    df_nonzero = df[df["value"].apply(lambda v: v != 0 and v != (0, 0))]

    if df_nonzero.empty:
        print(f"[INFO] No non-zero entries found in {reg_name}.")
        return

    # Sort by value (handle int or tuple)
    df_sorted = df_nonzero.sort_values(
        by="value",
        key=lambda col: col.apply(lambda v: sum(v) if isinstance(v, tuple) else v),
        ascending=False
    )

    if csv_path:
        df_sorted.to_csv(csv_path, index=False)
        print(f"[INFO] Wrote {len(df_sorted)} entries to {csv_path}")

    print(f"\n[INFO] Top {top_k} entries in {reg_name}:")
    print(df_sorted.head(top_k))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clear or read telemetry registers.")
    parser.add_argument("--mode", choices=["clear", "read"], default="clear", help="Operation mode")
    parser.add_argument("--output", type=str, help="CSV file path to save register values (read mode only)")
    parser.add_argument("--top-k", type=int, default=10, help="Show top-K register entries (read mode only)")
    args = parser.parse_args()

    c = Controller()
    register_names = ["Egress.IntStats.packet_count_register", "Egress.IntStats.byte_count_register"]
    c.setup_tables(register_names)

    if args.mode == "clear":
        for reg in register_names:
            c.clear_register(reg)

    elif args.mode == "read":
        for reg in register_names:
            out_path = args.output or f"{reg.replace('.', '_')}.csv"
            dump_register_df(c=c, reg_name=reg, csv_path=out_path, top_k=args.top_k)

    c.tear_down()
