from banking_system import BankingSystem
from typing import Dict

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
        self._balances: Dict[str, int] = {} #current balance of the account (maps account_id)
        self._outgoing_total: Dict[str, int] = {} #total amount account has sent out (maps account_id)
    
    # time complexity of O(1)
     def create_account(self, timestamp: int, account_id: str) -> bool: 
        if account_id in self._balances:
            return False
        self._balances[account_id] = 0
        self._outgoing_total[account_id] = 0
        return True

    # time complexity of O(1)
     def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None: 
        balance = self._balances.get(account_id) #looks up the balance in the account
        if balance is None: #when account does not exist
            return None
        # Assuming non-negative amounts
        balance += amount
        self._balances[account_id] = balance
        return balance

    # time complexity of O(1)
     def transfer(self, timestamp: int, source_account_id: str, target_account_id: str, amount: int) -> int | None:
       #checking if the accounts exisit, and making sure they are not the same account
        if (
            source_account_id not in self._balances
            or target_account_id not in self._balances
            or source_account_id == target_account_id
        ): 
            return None
        #sournce account does not have sufficient funds, the transfer will not happen
        if self._balances[source_account_id] < amount:
            return None

        #performing the transfer (subtract from source and add to target)
        self._balances[source_account_id] -= amount
        self._balances[target_account_id] += amount

        # added this for Level 2 to help with top_spenders function
        self._outgoing_total[source_account_id] += amount
        
        return self._balances[source_account_id]

    # Level 2
     def top_spenders(self, timestamp: int, n: int) -> list[str]:
        
        # Build list from existing accounts to ensure brand-new accounts show as 0
        
        #list of tuples to have acount ID and the total outgoing ammount
        top_accounts = []
        for acc_id in self._balances.keys():
            total_outgoing = self._outgoing_total.get(acc_id, 0) #get 0 if account id is not in outgoing_total
            tuple_pair = (acc_id, total_outgoing)
            top_accounts.append(tuple_pair)

        #sorts the higher outgoing total first
        top_accounts.sort(key=lambda item: (-item[1], item[0]))

        #slices to keep top n entries
        top_accounts = top_accounts[:n]

        return [f"{acc_id}({total})" for acc_id, total in top_accounts]
