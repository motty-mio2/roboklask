from python.domain import McuConnection
from python.domain.config import OutputType, settings

from .null_connection import NullMcuConnection
from .serial_connection import SerialMcuConnection


def get_mcu_connection() -> McuConnection:
    out_type = settings.output_type
    print(f"MCU Connection type: {out_type}")
    match out_type:
        case OutputType.UART | OutputType.PPO:
            return SerialMcuConnection()
        case OutputType.BRIDGE:
            from .bridge_connection import BridgeMcuConnection

            return BridgeMcuConnection()
        case _:
            return NullMcuConnection()
