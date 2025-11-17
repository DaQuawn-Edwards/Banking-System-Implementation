from banking_system import BankingSystem
from typing import Dict, Optional

class BankingSystemImpl(BankingSystem):
     """
    Level 1 implementation:
      - create_account
      - deposit
      - transfer
    Notes:
      * Timestamps are accepted but not used for Level 1 logic.
      * Balances are stored as non-negative integers.
    """
     def __init__(self) -> None:
        self._balances: Dict[str, int] = {}
        self._outgoing: Dict[str, int] = {}
    # O(1)
     def create_account(self, timestamp: int, account_id: str) -> bool: 
        if account_id in self._balances:
            return False
        self._balances[account_id] = 0
        self._outgoing[account_id] = 0
        return True

    # O(1)
     def deposit(self, timestamp: int, account_id: str, amount: int) -> Optional[int]: 
        bal = self._balances.get(account_id)
        if bal is None:
            return None
        # Assuming non-negative amounts per spec/tests
        bal += amount
        self._balances[account_id] = bal
        return bal

    # O(1)
     def transfer(
        self,
        timestamp: int,
        source_account_id: str,
        target_account_id: str,
        amount: int,
    ) -> Optional[int]:
        if (
            source_account_id not in self._balances
            or target_account_id not in self._balances
            or source_account_id == target_account_id
        ):
            return None
        if self._balances[source_account_id] < amount:
            return None

        self._balances[source_account_id] -= amount
        self._balances[target_account_id] += amount

        # Level 2: record outgoing for the source
        self._outgoing[source_account_id] += amount
        return self._balances[source_account_id]

    # -------- Level 2 --------
     def top_spenders(self, timestamp: int, n: int) -> list[str]:
        """
        Return top n accounts by total outgoing (desc),
        tie-broken by account_id (asc). Include accounts with 0 outgoing.
        Format: ["account_id(total)"].
        """
        # Build list from existing accounts to ensure brand-new accounts show as 0
        items = [(aid, self._outgoing.get(aid, 0)) for aid in self._balances.keys()]
        items.sort(key=lambda t: (-t[1], t[0]))  # total desc, id asc
        items = items[:n]
        return [f"{aid}({total})" for aid, total in items]


test = BankingSystemImpl()
# Test Level 2
print(test.create_account(1, "account3"))
print(test.create_account(2, "account2"))
print(test.create_account(3, "account1"))
print(test.deposit(4, "account1", 2000))
print(test.deposit(5, "account2", 3000))
print(test.deposit(6, "account3", 4000))
print(test.top_spenders(7, 3))
print(test.transfer(8, "account3", "account2", 500))
print(test.transfer(9, "account3", "account1", 1000))
print(test.transfer(10, "account1", "account2", 2500))
print(test.top_spenders(11, 3))