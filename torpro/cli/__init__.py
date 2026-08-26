"""CLI and TUI presentation layer package."""

__all__ = ["main", "TuiDashboard"]


def main():
    from torpro.cli.main import main as _main
    return _main()


def TuiDashboard():
    from torpro.cli.tui import TuiDashboard as _TuiDashboard
    return _TuiDashboard()
