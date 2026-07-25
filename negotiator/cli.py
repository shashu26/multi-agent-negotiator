"""Command-line entry point: python -m negotiator.cli [options]"""

import argparse

from .agent import NegotiatorAgent
from .engine import run_negotiation


def main():
    parser = argparse.ArgumentParser(description="Run a two-agent A2A negotiation demo.")
    parser.add_argument("--item", default="a vintage acoustic guitar", help="What's being negotiated")
    parser.add_argument("--buyer-target", type=float, default=300.0)
    parser.add_argument("--buyer-max", type=float, default=450.0, help="Buyer's reservation (walk-away) price")
    parser.add_argument("--seller-target", type=float, default=500.0)
    parser.add_argument("--seller-min", type=float, default=380.0, help="Seller's reservation (walk-away) price")
    parser.add_argument("--rounds", type=int, default=10)
    args = parser.parse_args()

    buyer = NegotiatorAgent(
        name="BuyerAgent", role="buyer", item=args.item,
        reservation_price=args.buyer_max, target_price=args.buyer_target,
        style="polite but budget-conscious",
    )
    seller = NegotiatorAgent(
        name="SellerAgent", role="seller", item=args.item,
        reservation_price=args.seller_min, target_price=args.seller_target,
        style="friendly but protective of margin",
    )

    mode = "LLM-backed (Claude)" if buyer.is_llm_backed else "heuristic fallback (no ANTHROPIC_API_KEY found)"
    print(f"Starting negotiation over: {args.item}")
    print(f"Mode: {mode}\n")

    result = run_negotiation(buyer, seller, max_rounds=args.rounds)
    print(result.summary())


if __name__ == "__main__":
    main()
