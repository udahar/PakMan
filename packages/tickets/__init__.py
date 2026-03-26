"""Tickets - Ticket tracking and management."""

__version__ = "1.0.0"

from .tickets import TicketManager, Ticket, TicketStatus, TicketPriority, create_ticket, list_tickets

__all__ = ["TicketManager", "Ticket", "TicketStatus", "TicketPriority", "create_ticket", "list_tickets"]
