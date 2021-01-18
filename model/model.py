#!/usr/bin/env python3

"""
model.py: agent-based model ESD system behavior
"""

import collections
import random

class Agent:
    """
    Represents an agent. Tracks all the agent's balances.
    """
    
    def __init__(self):
        # ESD balance
        self.esd = 0.0
        # USDC balance
        self.usdc = 0.0
        # ESDS (Dao share) balance
        self.esds = 0.0
        # Eth balance
        self.eth = 0.0
        # Uniswap LP share balance
        self.lp = 0.0
        # Coupon underlying part by expiration epoch
        self.underlying_coupons = collections.defaultdict(float)
        # Coupon premium part by expiration epoch
        self.premium_coupons = collections.defaultdict(float)
        
    def __str__(self):
        """
        Turn into a readable string summary.
        """
        return "Agent(esd={:.2f}, usdc={:.2f}, esds={}, eth={}, lp={})".format(self.esd, self.usdc, self.eth, self.lp)
        
    def get_strategy(self, price):
        """
        Get weights, as a dict from action to float, as a function of the price.
        """
        
        strategy = collections.defaultdict(lambda: 1.0)
        
        # TODO: real (learned? adversarial? GA?) model of the agents
        # TODO: agent preferences/utility function
        
        if price > 1.0:
            # Expansion so we want to bond
            strategy["bond"] = 2.0
        
        return strategy

class UniswapPool:
    """
    Represents the Uniswap pool. Tracks ESD and USDC balances of pool, and total outstanding LP shares.
    """
    
    def __init__(self):
        # ESD balance
        self.esd = 0.0
        # USDC balance
        self.usdc = 0.0
        # Total shares
        self.total_shares = 0.0
        
    def operational(self):
        """
        Return true if buying and selling is possible.
        """
        
        return self.esd > 0 and self.usdc > 0
    
    def esdPrice(self):
        """
        Get the current ESD price in USDC.
        """
        
        if self.operational():
            return self.usdc / self.esd
        else:
            return 1.0
        
    def deposit(self, esd, usdc):
        """
        Deposit the given number of ESD and USDC. Returns the number of new LP shares minted.
        """
        
        # TODO: get the real uniswap deposit logic
        
        new_value = esd * self.esdPrice() + usdc
        held_value = self.esd * self.esdPrice() + self.usdc
        if held_value > 0:
            new_shares = self.total_shares / held_value * new_value
        else:
            new_shares = 1
        
        self.esd += esd
        self.usdc += usdc
        self.total_shares += new_shares
        
        return new_shares
        
    def withdraw(self, shares):
        """
        Withdraw the given number of shares. Gets a balanced amount of ESD and USDC.
        Returns a tuple of (ESD, USDC)
        """
        # TODO: get the real uniswap withdraw logic
        portion = shares / self.total_shares
        
        esd = portion * self.esd
        usdc = portion * self.usdc
        
        self.total_shares = max(0, self.total_shares - shares)
        self.esd = max(0, self.esd - esd)
        self.usdc = max(0, self.usdc - usdc)
        
        return (esd, usdc)
        
    def buy(self, usdc):
        """
        Spend the given number of USDC to buy ESD. Returns the ESD bought.
        """
        
        # TODO: get real uniswap logic
        
        k = self.esd * self.usdc
        
        new_esd = k / (self.usdc + usdc)
        esd = self.esd - new_esd
        
        self.usdc += usdc
        self.esd = new_esd
        
        return esd
        
    def sell(self, esd):
        """
        Sell the given number of ESD for USDC. Returns the USDC received.
        """
        
        # TODO: get real uniswap logic
        
        k = self.esd * self.usdc
        
        new_usdc = k / (self.esd + esd)
        usdc = self.usdc - new_usdc
        
        self.esd += esd
        self.usdc = new_usdc
        
        return usdc
        
class DAO:
    """
    Represents the ESD DAO. Tracks ESD balance of DAO and total outstanding ESDS.
    """
    
    def __init__(self):
        # How many ESD are bonded
        self.esd = 0.0
        # How many ESD exist?
        self.esd_supply = 0.0
        # How many shares are outstanding
        self.total_shares = 0.0
        # What epoch is it?
        self.epoch = -1
        # What block did the epoch start
        self.epoch_block = 0
        # Are we expanding or contracting
        self.expanding = False
        
        # TODO: add real interest/debt/coupon model
        self.interest = 0.01
        self.debt = 0.0
        
    def bond(self, esd):
        """
        Deposit and bond the given amount of ESD.
        Returns the number of ESDS minted.
        """
    
        # TODO: model lockups
        
        if self.esd > 0:
            new_shares = self.total_shares / self.esd * esd
        else:
            new_shares = 1.0
        
        self.esd += esd
        self.total_shares += new_shares
        
        return new_shares
        
    def unbond(self, shares):
        """
        Unbond and withdraw the given number of shares.
        Returns the amount of ESD received.
        """
        
        # TODO: model lockups
        
        portion = shares / self.total_shares
        
        esd = self.esd * portion
        
        self.total_shares = max(0, self.total_shares - shares)
        self.esd = max(0, self.esd - esd)
        
        return esd
        
    def fee(self):
        """
        How much does it cost in ETH to advance, probably.
        """
        
        return 0.001
        
    def can_advance(self, block: int):
        """
        Return True if we can advance at the given block, and False otherwise.
        """
        
        # TODO: Use real parameter
        return block - self.epoch_block >= 10 or self.epoch == -1
        
    def advance(self, block: int, eth: float, uniswap: UniswapPool) -> float:
        """
        Advance the ESD epoch, at the given block, spending the given amount of
        ETH. Returns the ESD advance reward.
        
        Needs access to Uniswap to get the proce
        """
        
        assert(self.can_advance(block))
        self.epoch_block = block
        assert(eth == self.fee())
        
        # Ignore the consumed eth
        
        self.epoch += 1
        
        if uniswap.esdPrice() >= 1.0:
            self.expanding = True
        else:
            self.expanding = False
            
        if self.expanding:
            new_esd = self.interest * self.esd
            self.esd += new_esd
            self.esd_supply += new_esd
            self.debt = 0
        else:
            # TODO: real debt model probably wants total ESD supply
            self.debt += self.esd_supply * 0.01
        
        reward = 1000
        self.esd_supply += reward
        
        return reward
        
    # TODO: model LP rewards
    
class Model:
    """
    Full model of the economy.
    """
    
    def __init__(self):
        self.uniswap = UniswapPool()
        self.dao = DAO()
        self.agents = []
        for i in range(20):
            agent = Agent()
            # Give everyone some ETH and USDC to start
            agent.eth = 1.0
            agent.usdc = 1000
            self.agents.append(agent)
        
        # Track time in blocks
        self.block = 0
        
    def step(self):
        """
        Step the model by one block. Let all the agents act.
        
        Returns True if anyone could act.
        """
        
        self.block += 1
        
        print("Block {}, epoch {}, price {:.2f}, supply {:.2f}, bonded {:.2f}, liquidity {:.2f} ESD / {:.2f} USDC".format(
            self.block, self.dao.epoch, self.uniswap.esdPrice(), self.dao.esd_supply, self.dao.esd, self.uniswap.esd, self.uniswap.usdc))
        
        anyone_acted = False
        for agent_num, a in enumerate(self.agents):
            # TODO: real strategy
            
            options = []
            if a.usdc > 0 and self.uniswap.operational():
                options.append("buy")
            if a.esd > 0 and self.uniswap.operational():
                options.append("sell")
            if a.eth >= self.dao.fee() and self.dao.can_advance(self.block):
                options.append("advance")
            if a.esd > 0:
                options.append("bond")
            if a.esds > 0:
                options.append("unbond")
            if a.usdc > 0 and a.esd > 0:
                options.append("deposit")
            if a.lp > 0:
                options.append("withdraw")
                
            # TODO: coupons
                
            if len(options) > 0:
                # We can act
        
                strategy = a.get_strategy(self.uniswap.esdPrice())
                
                weights = [strategy[o] for o in options]
                
                action = random.choices(options, weights=weights)[0]
                
                print("Agent {}: {}".format(agent_num, action))
                
                if action == "buy":
                    usdc = a.usdc * random.random()
                    esd = self.uniswap.buy(usdc)
                    a.usdc -= usdc
                    a.esd += esd
                    print("Buy {:.2f} ESD for {:.2f} USDC".format(esd, usdc))
                elif action == "sell":
                    esd = a.esd * random.random()
                    usdc = self.uniswap.sell(esd)
                    a.esd -= esd
                    a.usdc += usdc
                    print("Sell {:.2f} ESD for {:.2f} USDC".format(esd, usdc))
                elif action == "advance":
                    fee = self.dao.fee()
                    esd = self.dao.advance(self.block, fee, self.uniswap)
                    a.eth -= fee
                    a.esd += esd
                    print("Advance for {:.2f} ESD".format(esd))
                elif action == "bond":
                    esd = a.esd * random.random()
                    esds = self.dao.bond(esd)
                    a.esd -= esd
                    a.esds += esds
                    print("Bond {:.2f} ESD".format(esd))
                elif action == "unbond":
                    esds = a.esds * random.random()
                    esd = self.dao.unbond(esds)
                    a.esds -= esds
                    a.esd += esd
                    print("Unond {:.2f} ESD".format(esd))
                elif action == "deposit":
                    price = self.uniswap.esdPrice()
                    
                    if a.esd * price < a.usdc:
                        esd = a.esd * random.random()
                        usdc = esd * price
                    else:
                        usdc = a.usdc * random.random()
                        esd = usdc / price
                    lp = self.uniswap.deposit(esd, usdc)
                    a.esd = max(0, a.esd - esd)
                    a.usdc = max(0, a.usdc - usdc)
                    a.lp += lp
                    print("Provide {:.2f} ESD and {:.2f} USDC".format(esd, usdc))
                elif action == "withdraw":
                    lp = a.lp * random.random()
                    (esd, usdc) = self.uniswap.withdraw(lp)
                    a.lp -= lp
                    a.esd += esd
                    a.usdc += usdc
                    print("Stop providing {:.2f} ESD and {:.2f} USDC".format(esd, usdc))
                else:
                    raise RuntimeError("Bad action: " + action)
                    
                anyone_acted = True
            else:
                print("Agent {} cannot act!".format(agent_num))
        return anyone_acted
        

def main():
    """
    Main function: run the simulation.
    """
    
    model = Model()
    
    for i in range(100):
        if not model.step():
            # Nobody could act
            break
    
if __name__ == "__main__":
    main()
