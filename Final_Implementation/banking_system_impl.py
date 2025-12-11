from banking_system import BankingSystem

class BankingSystemImpl(BankingSystem):
    """
    Implementation for:
        1) Level 1: create_account, deposit, transfer
        2) Level 2: top_spenders
        3) Level 3: pay, get_payment_status
        4) Level 4: merge_accounts, get_balance
    """
    def __init__(self) -> None:
        # Key: account_id
        # Value: dict { 
        #    "balance": int, 
        #    "transactions": list, 
        #    "creation_time": int,
        #    "merged_at": int
        # }

        '''
        # Example structure in tree
        whole_accounts: dict
        │
        ├── key: account_id (str)
        │      value: account_info (dict)
        │
        │ account_info
        │ ├── "balance": int
        │ └── "transactions": list
        │        └── transaction dict:
        │             ├── "timestamp": int
        │             ├── "operation": str
        │             ├── "amount": int     
        |             ├── "payment": str    # only in payback transactions, stores the unique payment number (num_payment) generated in pay()
        │             └── "deposited": bool     # only in payback transactions, tracks if cashback has deposited or not
        '''
        self.whole_accounts = {}
        self.payment_counter = 1
        self.MILLISECONDS_IN_1_DAY = 86400000

    def _process_cashbacks(self, timestamp: int) -> None:
        """
        Go through all scheduled cashback transactions stored inside whole_accounts,
        and deposit any cashback whose due timestamp <= current timestamp,
        and which has not yet been deposited.
        """
        for account_info in self.whole_accounts.values():
            for transaction in account_info["transactions"]:
                if (
                    transaction["operation"] == "cashback"
                    and transaction["timestamp"] <= timestamp
                    and transaction["deposited"] is False
                ):
                    # deposit cashback
                    account_info["balance"] += transaction["amount"]
                    transaction["deposited"] = True

    def create_account(self, timestamp: int, account_id: str) -> bool:
        # If ID exists
        if account_id in self.whole_accounts:
            #if exisiting acount is active and not merged then no creation
            if "merged_at" not in self.whole_accounts[account_id]:
                return False
            # If old account was merged we can create a new account with same ID

        #Intializing new account
        self.whole_accounts[account_id] = {
            "balance": 0,
            "transactions": [],
            "creation_time": timestamp
        }
        return True

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        """
        Deposit `amount` into `account_id` at the given `timestamp`

        Returns:
        - Updated balance (int) if the deposit succeeds
        - None if the account does not exist or has been merged/closed
        """

        self._process_cashbacks(timestamp)
        
        #checking if account exists
        if account_id not in self.whole_accounts:
            return None
        
        account = self.whole_accounts[account_id]

        #if it is merged then account is not acctive
        if "merged_at" in account:
            return None

         #apply deposit to account balance   
        account["balance"] += amount

        #record deposity in transaction history for future methods
        account["transactions"].append({
            "timestamp": timestamp,
            "operation": "deposit",
            "amount": amount
        })

        #return new balance
        return account["balance"]

    def transfer(self, timestamp: int, source_account_id: str, target_account_id: str, amount: int) -> int | None:
        self._process_cashbacks(timestamp)
        """
        Transfer `amount` of money from `source_account_id` to `target_account_id`
        at the given `timestamp`.

        Returns:
        - Updated balance of the source account if the transfer succeeds
        - None if the transfer is invalid or cannot be completed
        """
        
        #accounts have to exist and source and target are different accounts
        if (source_account_id not in self.whole_accounts or 
            target_account_id not in self.whole_accounts or 
            source_account_id == target_account_id):
            return None
            
        source = self.whole_accounts[source_account_id]
        target = self.whole_accounts[target_account_id]
        
        # Check if either source or target is merged
        if "merged_at" in source or "merged_at" in target:
            return None
        
        #source should have enough money to do the transfer
        if source["balance"] < amount:
            return None
        
        source["balance"] -= amount
        target["balance"] += amount
        
        #recording outgoing transfer in account history
        source["transactions"].append({
            "timestamp": timestamp,
            "operation": "transfer_out",
            "amount": amount,
            "target": target_account_id
        })

        #recording incoming transfer in target account history
        target["transactions"].append({
            "timestamp": timestamp,
            "operation": "transfer_in",
            "amount": amount,
            "source": source_account_id
        })
        
        #return updated balance of source
        return source["balance"]

    def top_spenders(self, timestamp: int, n: int) -> list[str]:
        """
        Return a list of the top `n` spending accounts at the given `timestamp`.
    
        A spender is defined by the total amount of money that has gone out of the
        account:
        - outgoing transfers 
        - card payments
    
        The result is sorted by:
        -total outgoing amount in descending order
        -account id in ascending order (for ties)
    
        Each entry is formatted as "account_id(amount)".
        """
        self._process_cashbacks(timestamp)
        
        spenders = []

        #iterate over known accounts
        for acc_id, info in self.whole_accounts.items():
            # Skip accounts that are merged
            if "merged_at" in info:
                continue
                
            total_outgoing = 0
            #sum the out going money
            for transac in info["transactions"]:
                operation = transac["operation"]
                if operation == "transfer_out" or operation.startswith("payment"):
                    total_outgoing += transac["amount"]
            #storing so that the largest outgoing is first
            spenders.append((-total_outgoing, acc_id))
            
        spenders.sort()
        
        #final list
        result = []
        for i in range(min(n, len(spenders))):
            amt = -spenders[i][0]
            acc = spenders[i][1]
            result.append(f"{acc}({amt})")
            
        return result

    def pay(self, timestamp: int, account_id: str, amount: int) -> str | None:
        """
        Process a payment from an account and schedule a cashback reward
    
        Returns:
            payment_id (str) like "payment1" if successful
            None if the account doesn't exist, was merged, or has insufficient funds
        """
        self._process_cashbacks(timestamp)
        
        #accont has to exist and not be merged
        if account_id not in self.whole_accounts:
            return None
            
        account = self.whole_accounts[account_id]
        if "merged_at" in account:
            return None

        #enough money in the account to pay   
        if account["balance"] < amount:
            return None
        
        #unique payment ID
        payment_id = f"payment{self.payment_counter}"
        self.payment_counter += 1
        
        #deducting the payment amount
        account["balance"] -= amount
        
        account["transactions"].append({
            "timestamp": timestamp,
            "operation": payment_id,
            "amount": amount
        })
        
        #cashback happens one day later
        cashback_amount = int(amount * 0.02)
        account["transactions"].append({
            "timestamp": timestamp + self.MILLISECONDS_IN_1_DAY,
            "operation": "cashback",
            "amount": cashback_amount,
            "related_payment": payment_id,
            "deposited": False
        })
        
        return payment_id

    def get_payment_status(self, timestamp: int, account_id: str, payment: str) -> str | None:
        """
        Return the status of a payment made by an account.

        Possible returns:
            - "IN_PROGRESS"      
            - "CASHBACK_RECEIVED" 
            - None              
        """
        self._process_cashbacks(timestamp)
        
        #checking if account exists and not merged
        if account_id not in self.whole_accounts:
            return None
            
        account = self.whole_accounts[account_id]
        if "merged_at" in account:
            return None
        
        # Check transaction history
        payment_found = False
        cashback_deposited = False
        
        #searching transaction history
        for transac in account["transactions"]:
            if transac["operation"] == payment:
                payment_found = True
            if (transac["operation"] == "cashback" and 
                transac.get("related_payment") == payment and 
                transac["deposited"]):
                cashback_deposited = True
                
        if not payment_found:
            return None
        #If cashback was deposited then DONE otherwise still processing  
        return "CASHBACK_RECEIVED" if cashback_deposited else "IN_PROGRESS"

    def merge_accounts(self, timestamp: int, account_id_1: str, account_id_2: str) -> bool:
        """
        Merge account_id_2 into account_id_1.

        - account_id_1 absorbs the balance and transaction history of account_id_2
        - account_id_2 is marked as merged (soft-deleted)
        - Future operations on account_id_2 should fail
        - Historical queries (get_balance with old time_at) should still work
        """
        self._process_cashbacks(timestamp)
        
        #check that account is not the same
        if account_id_1 == account_id_2:
            return False
        
        #accounts should exisit
        if account_id_1 not in self.whole_accounts or account_id_2 not in self.whole_accounts:
            return False
            
        account_1 = self.whole_accounts[account_id_1]
        account_2 = self.whole_accounts[account_id_2]
        
        # Cannot merge if either is already merged
        if "merged_at" in account_1 or "merged_at" in account_2:
            return False
        
        #move balance from account 1 to account 2
        account_1["balance"] += account_2["balance"]
        
        #copy and tag account transation into acocunt 1
        for transac in account_2["transactions"]:
            new_transac = transac.copy()
            new_transac["merged_from"] = account_id_2
            new_transac["merged_at"] = timestamp
            account_1["transactions"].append(new_transac)
            
        # Delete account 2 so it does not accept new operations
        account_2["merged_at"] = timestamp
        
        return True

    def get_balance(self, timestamp: int, account_id: str, time_at: int) -> int | None:
        """
        Return the balance that `account_id` had at the historical time `time_at`.

        This method must:
        - ignore transactions that occur after `time_at`
        - include merged-in transactions only if the merge happened before `time_at`
        - treat a merged account as non-existent for queries at or after its merge time
        - treat an account as non-existent before its creation time
        """
        self._process_cashbacks(timestamp)
        
        if account_id not in self.whole_accounts:
            return None
            
        account = self.whole_accounts[account_id]
        
        #check if account exisits at time requested
        if account["creation_time"] > time_at:
            return None
            
        #account only exisits for timestamps before the merge
        if "merged_at" in account:
            if time_at >= account["merged_at"]:
                return None
        
        #balance calculcated
        balance = 0
        for transac in account["transactions"]:
            #skipping for future transactions
            if transac["timestamp"] > time_at:
                continue
                
            #if transaction belonged to another account, count if merge was before or at the time given
            if "merged_at" in transac:
                if transac["merged_at"] > time_at:
                    continue
            
            operation = transac["operation"]
            amount = transac["amount"]
            
            if operation == "deposit":
                balance += amount
            elif operation == "transfer_in":
                balance += amount
            elif operation == "transfer_out":
                balance -= amount
            elif operation.startswith("payment"):
                balance -= amount
            elif operation == "cashback":
                balance += amount
                
        return balance
