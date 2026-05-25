"""Typed row helpers for monitors and users."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    email: str
    role: str
    approved: int
    appwrite_uid: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "User":
        return cls(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            role=row['role'],
            approved=row['approved'],
            appwrite_uid=row.get('appwrite_uid'),
        )


@dataclass
class Monitor:
    id: int
    slug: str
    pm_question: Optional[str]
    ticker: str
    description: Optional[str]
    signal_thresh_pp: float
    cooldown_hrs: float
    active: int
    created_at: str

    @classmethod
    def from_row(cls, row: dict) -> "Monitor":
        return cls(
            id=row['id'],
            slug=row['slug'],
            pm_question=row.get('pm_question'),
            ticker=row['ticker'],
            description=row.get('description'),
            signal_thresh_pp=row['signal_thresh_pp'],
            cooldown_hrs=row['cooldown_hrs'],
            active=row['active'],
            created_at=row['created_at'],
        )


@dataclass
class Signal:
    id: int
    monitor_id: int
    signal_ts: str
    pm_ts: str
    pm_prob_before: float
    pm_prob_after: float
    pm_move_pp: float
    direction: str
    predicted_eq_return_bps: float
    confidence: str
    status: str
    created_at: str

    @classmethod
    def from_row(cls, row: dict) -> "Signal":
        return cls(
            id=row['id'],
            monitor_id=row['monitor_id'],
            signal_ts=row['signal_ts'],
            pm_ts=row['pm_ts'],
            pm_prob_before=row['pm_prob_before'],
            pm_prob_after=row['pm_prob_after'],
            pm_move_pp=row['pm_move_pp'],
            direction=row['direction'],
            predicted_eq_return_bps=row['predicted_eq_return_bps'],
            confidence=row.get('confidence', 'MEDIUM'),
            status=row.get('status', 'active'),
            created_at=row['created_at'],
        )
