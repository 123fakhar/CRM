from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"
    CLOSER = "closer"


class InitialStatus(str, Enum):
    PENDING = "Pending"


class BuyerResponse(str, Enum):
    PENDING_NOT_RECEIVED = "Pending / Not Received"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    NO_TARGET = "No Target"
    DUPLICATE = "Duplicate"
    INVALID = "Invalid"
    OTHER = "Other"


class FinalStatus(str, Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"


class RejectionReason(str, Enum):
    DUPLICATE_LEAD = "Duplicate Lead"
    INVALID_PHONE = "Invalid Phone"
    INVALID_INFORMATION = "Invalid Information"
    CUSTOMER_NOT_INTERESTED = "Customer Not Interested"
    OUTSIDE_SERVICE_AREA = "Outside Service Area"
    BUYER_REJECTED = "Buyer Rejected"
    DID_NOT_QUALIFY = "Did Not Qualify"
    NO_TARGET = "No Target"
    OTHER = "Other"


US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
]
