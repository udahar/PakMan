"""
Leaderboard Display

Formats and displays tournament leaderboards.
"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from kofh.throne import ThroneHolder


class Leaderboard:
    """Formats and displays leaderboards."""
    
    @staticmethod
    def format_leaderboard(
        role: str,
        holders: list["ThroneHolder"],
        title: Optional[str] = None,
    ) -> str:
        """
        Format a leaderboard as ASCII table.
        
        Args:
            role: The role name
            holders: List of throne holders (sorted by score)
            title: Optional custom title
        
        Returns:
            Formatted ASCII table string
        """
        if not title:
            title = f"{role.upper()} THRONE LEADERBOARD"
        
        lines = []
        lines.append("╔" + "═" * 60 + "╗")
        lines.append(f"║  {title.center(56)}  ║")
        lines.append("╠" + "═" * 60 + "╣")
        
        if not holders:
            lines.append("║  (No holders yet)                                        ║")
        else:
            for i, holder in enumerate(holders[:10]):  # Top 10
                crown = "👑 " if holder.is_current and i == 0 else "  "
                rank = f"{i + 1}" if i > 0 else " "
                
                status = "KING" if holder.is_current else f"Defenses: {holder.defenses}"
                
                line = (
                    f"║  {crown}{rank}  {holder.model:<18} {holder.score:>5.1f}    "
                    f"{status:<15}  ║"
                )
                lines.append(line)
        
        lines.append("╚" + "═" * 60 + "╝")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_all_leaderboards(leaderboards: dict[str, list["ThroneHolder"]]) -> str:
        """Format all role leaderboards."""
        sections = []
        
        for role, holders in leaderboards.items():
            sections.append(Leaderboard.format_leaderboard(role, holders))
        
        return "\n\n".join(sections)
    
    @staticmethod
    def format_throne_swap(
        role: str,
        old_king: str,
        new_king: str,
        old_score: float,
        new_score: float,
    ) -> str:
        """Format a throne swap announcement."""
        diff = new_score - old_score
        
        lines = [
            "╔" + "═" * 60 + "╗",
            f"║  {'THRONE SWAP!':^56}  ║",
            "╠" + "═" * 60 + "╣",
            f"║  Role: {role:<52}  ║",
            f"║  Dethroned: {old_king:<46}  ║",
            f"║  New King: {new_king:<47}  ║",
            f"║  Score: {old_score:.1f} → {new_score:.1f} ({diff:+.1f}){'':>30}  ║",
            "╚" + "═" * 60 + "╝",
        ]
        
        return "\n".join(lines)
