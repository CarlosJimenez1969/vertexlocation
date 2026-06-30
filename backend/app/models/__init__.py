"""Registro de modelos SQLAlchemy."""
from app.models.user import User
from app.models.plan import Plan, Subscription
from app.models.device import Device
from app.models.pet import Pet
from app.models.position import Position
from app.models.geofence import Geofence
from app.models.mood import MoodState
from app.models.activity import DailyActivity
from app.models.alert import Alert
from app.models.report import VetReport
from app.models.password_reset import PasswordReset
from app.models.vehicle import Vehicle
from app.models.share_link import ShareLink

__all__ = [
    "User",
    "Plan",
    "Subscription",
    "Device",
    "Pet",
    "Position",
    "Geofence",
    "MoodState",
    "DailyActivity",
    "Alert",
    "VetReport",
    "PasswordReset",
    "Vehicle",
    "ShareLink",
]
