"""Checks the Python model against the course workbook."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import model as m  # noqa: E402


class ReproducesWorkbook(unittest.TestCase):
    def setUp(self):
        self.d = m.load()
        self.r = m.ratios(self.d)

    def test_statements(self):
        self.assertAlmostEqual(self.d["net_income"]["2026"], 27_425.25, places=2)
        self.assertAlmostEqual(self.d["total_assets"]["2026"], 680_400, places=0)
        self.assertAlmostEqual(self.d["equity"]["2026"], 300_873, places=0)

    def test_growth(self):
        self.assertAlmostEqual(self.r["2026"]["sales_growth"], 0.30, places=4)
        self.assertAlmostEqual(self.r["2025"]["sustainable_growth"], 0.0677, places=4)
        self.assertAlmostEqual(self.r["2026"]["sustainable_growth"], 0.0579, places=4)
        self.assertAlmostEqual(self.r["2026"]["payout"], 0.40, places=4)

    def test_liquidity_leverage(self):
        self.assertAlmostEqual(self.r["2026"]["current_ratio"], 2.161, places=3)
        self.assertAlmostEqual(self.r["2026"]["quick_ratio"], 0.9777, places=4)
        self.assertAlmostEqual(self.r["2026"]["debt_to_equity"], 0.8732, places=4)

    def test_trade_credit(self):
        t = m.trade_credit(self.d)
        self.assertAlmostEqual(t["purchases"], 437_050, places=0)
        self.assertAlmostEqual(t["discounts_forgone"], 8_741, places=0)
        self.assertAlmostEqual(t["discounts_share_of_net_income"], 0.2907, places=4)
        self.assertAlmostEqual(t["effective_cost"], 0.2786, places=4)
        self.assertAlmostEqual(t["effective_cost_after_tax"], 0.2090, places=4)
        self.assertAlmostEqual(t["cost_of_debt"], 0.07, places=2)

    def test_funding_balances(self):
        f = m.funding(self.d)
        self.assertAlmostEqual(f["asset_growth"], 130_100, places=0)


if __name__ == "__main__":
    unittest.main()
