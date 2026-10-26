"""
Pydantic schemas and models for WiFi Time Roulette.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DeviceModel(BaseModel):
    mac: str
    ip: str
    hostname: str = ""
    custom_name: str = ""
    vendor: str = ""
    device_type: str = "device"
    is_gateway: bool = False
    is_host: bool = False
    is_protected: bool = False
    status: str = "ACTIVE"  # ACTIVE, LOCKED_OUT, PROTECTED
    base_allowance_hours: float = 168.0
    remaining_seconds: float = 604800.0
    remaining_formatted: str = "168h 00m"
    reset_interval: str = "monthly"
    next_reset_at: Optional[str] = None
    last_seen_at: Optional[str] = None
    locked_out_at: Optional[str] = None
    decay_enabled: bool = False

class DeviceUpdateRequest(BaseModel):
    custom_name: Optional[str] = None
    is_protected: Optional[bool] = None
    base_allowance_hours: Optional[float] = None
    remaining_seconds: Optional[float] = None
    decay_enabled: Optional[bool] = None
    device_type: Optional[str] = None

class BetItem(BaseModel):
    # E.g. 'red', 'black', 'even', 'odd', 'low', 'high', 'dozen_1', 'col_1', 'straight'
    bet_type: str
    bet_selection: str  # 'red', 'black', 'even', 'odd', '1-18', '19-36', '1st12', '2nd12', '3rd12', 'col1', 'col2', 'col3', or number string '0'-'36'
    wager_seconds: float = Field(..., gt=0, description="Wager in seconds")
    wager_hours: float = Field(..., gt=0, description="Wager in hours")

class SpinRequest(BaseModel):
    device_mac: str
    bets: List[BetItem]

class BetOutcome(BaseModel):
    bet_type: str
    bet_selection: str
    wager_hours: float
    is_win: bool
    payout_multiplier: float
    profit_hours: float
    total_returned_hours: float

class SpinResponse(BaseModel):
    winning_number: int
    winning_color: str  # 'red', 'black', 'green'
    is_even: bool
    is_odd: bool
    is_low: bool       # 1-18
    is_high: bool      # 19-36
    dozen: int         # 1, 2, 3 or 0
    column: int        # 1, 2, 3 or 0
    total_wager_hours: float
    total_won_hours: float
    net_profit_hours: float
    balance_before_hours: float
    balance_after_hours: float
    balance_after_formatted: str
    is_busted: bool
    status: str
    bets_breakdown: List[BetOutcome]
    message: str

class SettingsUpdateRequest(BaseModel):
    enforcement_mode: Optional[str] = None
    default_allowance_hours: Optional[float] = None
    reset_interval: Optional[str] = None
    reset_day_of_month: Optional[int] = None
    active_decay_enabled: Optional[bool] = None
    decay_rate_multiplier: Optional[float] = None
    unifi_host: Optional[str] = None
    unifi_username: Optional[str] = None
    unifi_password: Optional[str] = None
    unifi_site: Optional[str] = None
    unifi_verify_ssl: Optional[bool] = None
    webhook_block_cmd: Optional[str] = None
    webhook_unblock_cmd: Optional[str] = None
    admin_pin: Optional[str] = None

class AdminActionRequest(BaseModel):
    admin_pin: Optional[str] = None
    reason: Optional[str] = "Admin Manual Action"
    hours_to_add: Optional[float] = 0.0

class TestEnforcementRequest(BaseModel):
    mac: str
    action: str  # 'block' or 'unblock'
