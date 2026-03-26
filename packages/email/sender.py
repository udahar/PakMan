"""
Email - Send emails via SMTP.

Usage:
    from email import EmailSender, EmailConfig, send_email
    
    config = EmailConfig(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        username="you@gmail.com",
        password="app_password"
    )
    sender = EmailSender(config)
    sender.send(
        to=["recipient@example.com"],
        subject="Alert",
        body="Server CPU at 95%"
    )
    
    # Quick send
    send_email("Subject", "Body", to=["recipient@example.com"])
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class EmailConfig:
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True


class EmailSender:
    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or self._load_config()
    
    def _load_config(self) -> EmailConfig:
        return EmailConfig(
            smtp_host=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.environ.get("SMTP_PORT", "587")),
            username=os.environ.get("SMTP_USERNAME", ""),
            password=os.environ.get("SMTP_PASSWORD", ""),
        )
    
    def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: bool = False,
        priority: str = "normal"
    ) -> Dict:
        if not self.config.username or not self.config.password:
            return {"success": False, "error": "Missing credentials"}
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.config.username
        msg["To"] = ", ".join(to)
        
        if priority == "high":
            msg["X-Priority"] = "1"
        elif priority == "low":
            msg["X-Priority"] = "5"
        
        content_type = "html" if html else "plain"
        msg.attach(MIMEText(body, content_type))
        
        try:
            server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
            if self.config.use_tls:
                server.starttls()
            server.login(self.config.username, self.config.password)
            server.sendmail(self.config.username, to, msg.as_string())
            server.quit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


def create_config(
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587,
    username: str = "",
    password: str = ""
) -> EmailConfig:
    """Create email configuration."""
    return EmailConfig(smtp_host, smtp_port, username, password)


def load_config() -> EmailConfig:
    """Load config from environment or return default."""
    return EmailConfig(
        smtp_host=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(os.environ.get("SMTP_PORT", "587")),
        username=os.environ.get("SMTP_USERNAME", ""),
        password=os.environ.get("SMTP_PASSWORD", ""),
    )


def send_email(
    subject: str,
    body: str,
    to: List[str],
    html: bool = False,
    priority: str = "normal"
) -> Dict:
    """Quick send email function."""
    config = load_config()
    sender = EmailSender(config)
    return sender.send(to, subject, body, html, priority)


__all__ = ["EmailSender", "EmailConfig", "create_config", "load_config", "send_email"]