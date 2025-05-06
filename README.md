# bfrt_controller

Reusable Python controller framework for programming Tofino switches via BFRT gRPC.

This module provides a high-level `Controller` interface over the BFRT gRPC API, supporting:
- Table entry management
- Multicast group programming
- Port configuration
- Utility functions for IP/MAC formatting

Site-specific setup helpers (e.g., port and multicast config) are provided under `helpers.py`. These assume the P4 pipeline and topology at the University of Waterloo testbed.

## Setup

```bash
sudo apt-get install python3-venv
python3 -m venv bfrt
source bfrt/bin/activate
pip install -r requirements.txt
```

## Usage Example

```python
from bfrt_controller import Controller
from bfrt_controller.helpers import setup_ports

c = Controller()
setup_ports(c)
c.setup_tables(["Ingress.Dmac.broadcast_table"])
```

## Acknowledgements
This controller design is based on [ACC-Turbo's original Tofino controller implementation](https://github.com/nsg-ethz/ACC-Turbo/blob/86869689a511567be5b42b4e556f3f6dc53f14be/tofino/python_controller/core.py) by the NSG group at ETH Zürich.
