"""StockAI CLI - Command Line Interface."""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def cmd_analyze(args):
    """Analyze stocks."""
    from data import StockDataLoader
    from analysis import StockAnalyzer

    print(f"Loading data for {len(args.symbols)} symbols...")

    loader = StockDataLoader(data_dir=args.data_dir)

    try:
        data = loader.load_multiple(args.symbols, period=args.period)
    except Exception as e:
        print(f"Error: {e}")
        return 1

    if not data:
        print("No data loaded")
        return 1

    print(f"\nAnalyzing {len(data)} stocks...")

    analyzer = StockAnalyzer()
    analyzer.load_data(data)
    metrics = analyzer.analyze_all()

    print("\n" + "=" * 70)
    print("  Analysis Results")
    print("=" * 70)

    for symbol, m in sorted(
        metrics.items(), key=lambda x: x[1].sharpe_ratio, reverse=True
    ):
        print(f"\n{symbol}:")
        print(f"  Price: ${m.current_price:.2f}")
        print(f"  Total Return: {m.total_return:.1%}")
        print(f"  Sharpe Ratio: {m.sharpe_ratio:.2f}")
        print(f"  Max Drawdown: {m.max_drawdown:.1%}")
        print(f"  Win Rate: {m.win_rate:.1%}")

    return 0


def cmd_top(args):
    """Show top stocks."""
    from data import StockDataLoader
    from analysis import StockAnalyzer

    loader = StockDataLoader(data_dir=args.data_dir)

    try:
        data = loader.load_multiple(args.symbols, period=args.period)
    except Exception as e:
        print(f"Error: {e}")
        return 1

    analyzer = StockAnalyzer()
    analyzer.load_data(data)
    analyzer.analyze_all()

    top = analyzer.get_top_performers("sharpe_ratio", top_n=args.count)

    print(f"\nTop {len(top)} Stocks by Sharpe Ratio:\n")

    for i, m in enumerate(top, 1):
        print(
            f"  {i}. {m.symbol}: {m.sharpe_ratio:.2f} Sharpe, {m.total_return:.1%} return"
        )

    return 0


def cmd_day_trading(args):
    """Day trading analysis."""
    from data import StockDataLoader
    from analysis.signals import DayTradingAnalyzer

    loader = StockDataLoader(data_dir=args.data_dir)

    try:
        data = loader.load_multiple(args.symbols, period="3mo")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    analyzer = DayTradingAnalyzer()
    top_signals = analyzer.get_top_signals(data, top_n=args.count)

    print(f"\nDay Trading Signals ({len(top_signals)} found)\n")
    analyzer.print_signals(top_signals)

    return 0


def cmd_long_term(args):
    """Long-term investment analysis."""
    from data import StockDataLoader
    from analysis.signals import LongTermAnalyzer
    import sys
    from pathlib import Path

    yf_path = Path(__file__).parent.parent / "yfinance-main" / "yfinance-main"
    if yf_path.exists() and str(yf_path) not in sys.path:
        sys.path.insert(0, str(yf_path))

    import yfinance as yf

    loader = StockDataLoader(data_dir=args.data_dir)

    try:
        data = loader.load_multiple(args.symbols, period="2y")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    info_dict = {}
    for symbol in args.symbols:
        try:
            ticker = yf.Ticker(symbol)
            info_dict[symbol] = ticker.info
        except:
            info_dict[symbol] = {}

    analyzer = LongTermAnalyzer()
    ratings = analyzer.analyze_multiple(data, info_dict)

    print(f"\nLong-Term Investment Ratings ({len(ratings)} stocks)\n")
    analyzer.print_ratings(ratings)

    return 0


def main():
    parser = argparse.ArgumentParser(description="StockAI - AI-Powered Stock Analysis")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    parser.add_argument("--data-dir", default="data", help="Data directory")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze stocks")
    analyze_parser.add_argument("symbols", nargs="+", help="Stock symbols")
    analyze_parser.add_argument("--period", default="5y", help="Time period")
    analyze_parser.set_defaults(func=cmd_analyze)

    top_parser = subparsers.add_parser("top", help="Show top stocks")
    top_parser.add_argument("symbols", nargs="+", help="Stock symbols")
    top_parser.add_argument("--count", type=int, default=10, help="Number to show")
    top_parser.add_argument("--period", default="5y", help="Time period")
    top_parser.set_defaults(func=cmd_top)

    day_parser = subparsers.add_parser("day-trading", help="Day trading signals")
    day_parser.add_argument("symbols", nargs="+", help="Stock symbols")
    day_parser.add_argument("--count", type=int, default=10, help="Number of signals")
    day_parser.set_defaults(func=cmd_day_trading)

    long_parser = subparsers.add_parser(
        "long-term", help="Long-term investment ratings"
    )
    long_parser.add_argument("symbols", nargs="+", help="Stock symbols")
    long_parser.set_defaults(func=cmd_long_term)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
