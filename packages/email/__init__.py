"""
Email Package — Send emails via SMTP from any project.

Supports Gmail (app passwords), Outlook, custom SMTP.
HTML + plain text, attachments, priority headers.

Usage:
    from email import EmailSender, load_config

    config = load_config()
    sender = EmailSender(config)

    sender.send(
        subject="Server alert",
        body="CPU usage hit 95%",
        priority="high"
    )

    # Or quick send
    from email import send_email
    send_email("Hello", "World", to=["recipient@example.com"])
"""

__version__ = "0.1.0"

try:
    from .sender import EmailSender, EmailConfig, load_config, create_config, send_email
    __all__ = [
        "EmailSender",
        "EmailConfig",
        "load_config",
        "create_config",
        "send_email",
    ]
except ImportError:
    import logging
    logging.warning("Email sender module not implemented yet")
    __all__ = []
