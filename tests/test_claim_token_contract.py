from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API_SOURCE = (ROOT / "custom_components/densial_nexus/api.py").read_text()
COORDINATOR_SOURCE = (ROOT / "custom_components/densial_nexus/coordinator.py").read_text()


class ClaimTokenContractTests(unittest.TestCase):
    def test_api_ack_requires_and_sends_claim_token(self):
        self.assertIn("claim_token: str", API_SOURCE)
        self.assertIn('"claim_token": claim_token', API_SOURCE)

    def test_coordinator_reads_database_command_id_and_claim_token(self):
        self.assertIn('command.get("command_id") or command.get("id")', COORDINATOR_SOURCE)
        self.assertIn('claim_token = command.get("claim_token")', COORDINATOR_SOURCE)

    def test_every_ack_path_forwards_claim_token(self):
        ack_lines = [
            line.strip()
            for line in COORDINATOR_SOURCE.splitlines()
            if "self.api.ack(" in line
        ]
        self.assertEqual(len(ack_lines), 4)
        for line in ack_lines:
            self.assertIn("command_id, claim_token,", line)

    def test_malformed_command_without_claim_token_fails_closed(self):
        self.assertIn("or not claim_token", COORDINATOR_SOURCE)


if __name__ == "__main__":
    unittest.main()
