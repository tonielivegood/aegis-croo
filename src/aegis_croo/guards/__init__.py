from src.aegis_croo.guards.base import BaseGuard
from src.aegis_croo.guards.exposure_guard import ExposureGuard
from src.aegis_croo.guards.gas_guard import GasGuard
from src.aegis_croo.guards.liquidity_guard import LiquidityGuard
from src.aegis_croo.guards.slippage_guard import SlippageGuard
from src.aegis_croo.guards.suspicious_pump_guard import SuspiciousPumpGuard
from src.aegis_croo.guards.unknown_token_guard import UnknownTokenGuard
from src.aegis_croo.guards.volatility_guard import VolatilityGuard
from src.aegis_croo.guards.volume_guard import VolumeGuard


DEFAULT_GUARDS: tuple[BaseGuard, ...] = (
    VolatilityGuard(),
    LiquidityGuard(),
    VolumeGuard(),
    ExposureGuard(),
    SlippageGuard(),
    GasGuard(),
    UnknownTokenGuard(),
    SuspiciousPumpGuard(),
)


__all__ = ["BaseGuard", "DEFAULT_GUARDS"]
