"""
uHAL access to the FCFD FPGA.

FCFD FPGA is a custom firmware for the KCU105 board.

The XML address table is the source of truth for register addresses.  This
module deliberately keeps the transport configuration separate from register
access so the same code can be used with a real KCU or an IPBus simulator.
"""

import argparse
from pathlib import Path
from typing import Any, Optional, Sequence

import logging

try:
    import uhal
except ModuleNotFoundError:
    print("Running without uhal (ipbus not installed with correct python bindings)")

class KCU:
    """Connect to an FCFD FPGA and access nodes from ``fcfd_fw.xml``."""
    
    DEFAULT_ADDRESS_TABLE = (
        Path(__file__).resolve().parent.parent
        / "fcfd_fw"
        / "address_tables"
        / "fcfd_fw.xml"
    )
    DEFAULT_URI = "ipbusudp-2.0://192.168.0.10:50001"

    def __init__(
        self,
        uri: str = DEFAULT_URI,
        address_table: str | Path = DEFAULT_ADDRESS_TABLE,
        device_id: str = "fcfd",
        uhal_level: str = "WARNING",
    ) :
        """Create a uHAL device using the supplied address table.

        uHAL is primarily useful for tests; when omitted, the
        installed uHAL Python bindings are imported at connection time.
        """
        table = Path(address_table).expanduser().resolve()
        if not table.is_file():
            raise FileNotFoundError(f"Address table not found: {table}")

        self.address_table = table
        self.uri = uri
        self.device_id = device_id
        self.uhal = uhal
        log_level_name = {
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "FATAL",
        }.get(uhal_level.upper())
        if log_level_name is None:
            valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
            raise ValueError(
                f"Invalid uHAL log level {uhal_level!r}; "
                f"choose one of {', '.join(valid_levels)}"
            )
        log_level = getattr(self.uhal.LogLevel, log_level_name)
        self.uhal.setLogLevelTo(log_level)
        self.hw = uhal.getDevice(
            device_id, uri, f"file://{table}"
        )

    def dispatch(self) -> None:
        """type=lambda s: getattr(logging, s.upper()),Send queued transactions to the FPGA."""
        self.hw.dispatch()

    def readable_nodes(self) -> list[str]:
        """Return readable leaf nodes from the address table."""
        return [
            node
            for node in self.hw.getNodes()
            if (
                not self.hw.getNode(node).getNodes()
                and self.hw.getNode(node).getPermission()
                != self.uhal.NodePermission.WRITE
            )
        ]

    def read_node(self, node: str, dispatch: bool = True) -> int:
        """Read a named address-table node and return uHAL's value object."""
        node_handle = self.hw.getNode(node)
        if node_handle.getPermission() == self.uhal.NodePermission.WRITE:
            raise PermissionError(f"Node is write-only and cannot be read: {node}")
        value = node_handle.read()
        if dispatch:
            self.dispatch()
        return int(value)


    def write_node(self, node: str, value: int, dispatch: bool = True) -> None:
        """Write a value to a named address-table node."""
        node_handle = self.hw.getNode(node)
        if node_handle.getPermission() == self.uhal.NodePermission.READ:
            raise PermissionError(f"Node is read-only and cannot be written: {node}")
        node_handle.write(value)
        if dispatch:
            self.dispatch()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read and write the FCFD FPGA over IPBus/uHAL."
    )
    parser.add_argument(
        "--ip", default="192.168.0.10", help="FPGA IP address (default: %(default)s)"
    )
    parser.add_argument(
        "--port", type=int, default=50001, help="IPBus UDP port (default: %(default)s)"
    )
    parser.add_argument(
        "--uri",
        help="Complete uHAL URI; overrides --ip and --port",
    )
    parser.add_argument(
        "--address-table",
        type=Path,
        default=KCU.DEFAULT_ADDRESS_TABLE,
        help="Address-table XML path (default: %(default)s)",
    )
    parser.add_argument(
        "--device-id", default="fcfd", help="uHAL device ID (default: %(default)s)"
    )
    
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")

    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        default="INFO",
        help="uHAL log level (default: %(default)s)",
    )
    
    parser.add_argument(
        "--read", "-r", 
        nargs='*',
        metavar="NODES", 
        help="Read nodes, use all to read all nodes")
    parser.add_argument(
        "--write", "-w", 
        nargs=2, 
        metavar=("NODE", "VALUE"), 
        help="Write a node"
    )

    parser.add_argument(
        "--nodes", "-n", 
        action="store_true", 
        help="List all address-table nodes")

    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    uri = args.uri or f"ipbusudp-2.0://{args.ip}:{args.port}"

    try:
        kcu = KCU(uri, args.address_table, args.device_id, args.log_level)

        if args.interactive:
            logging.info("Running in interactive mode")
            while True:
                print("\nEnter a mode:\n'w' -- write,\n'r' --- read,\n'n' -- list nodes,\n'e' --- exit.")
                mode = input(str())
                if mode == 'e':
                    return
                elif mode == 'n':
                    for node in kcu.hw.getNodes():
                        logging.info(node)
                elif mode == 'r':
                    while True:
                        print("Enter node(s) to read, separated by spaces, or 'all' to read all readable registers, or 'e' to return to mode selection:")
                        node = input(str())
                        if node == 'e':
                            break
                        if 'all' in node:
                            for node in kcu.readable_nodes():
                                value = kcu.read_node(node, dispatch=True)
                                logging.info(f"{node} = 0x{value:08x} ({value})")
                            continue
                        else:
                            for node in node.split():
                                value = kcu.read_node(node, dispatch=True)
                                logging.info(f"{node} = 0x{value:08x} ({value})")
                elif mode == 'w':
                    while True:
                        print("Enter node and value to write, separated by spaces or 'e' to return to mode selection:")
                        user_input = input(str())
                        if user_input == 'e':
                            break
                        node, value = user_input.split()
                        kcu.write_node(node, int(value, 16), dispatch=True)
                        logging.info(f"{node} <= 0x{int(value, 16):08x}")
                else:
                    print('Invalid mode. Please try again.')


        if args.nodes:
            for node in kcu.hw.getNodes():
                logging.info(node)
        if args.write:
            kcu.write_node(args.write[0], int(args.write[1],16), dispatch=True)
            logging.info(f"{args.write[0]} <= 0x{int(args.write[1],16):08x}")
        if args.read:
            if "all" in args.read:
                for node in kcu.readable_nodes():
                    print(f"reading {node}")
                    value = kcu.read_node(node, dispatch=True)
                    logging.info(f"{node} = 0x{value:08x} ({value})")
            else:
                for node in args.read:
                    value = kcu.read_node(node, dispatch=True)
                    logging.info(f"{node} = 0x{value:08x} ({value})")

    except (FileNotFoundError, PermissionError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    main()