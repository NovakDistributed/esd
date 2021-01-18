#!/usr/bin/env python3

"""
model.py: agent-based model ESD system behavior
"""

import collections
import random
import math

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
        return "Agent(esd={:.2f}, usdc={:.2f}, esds={}, eth={}, lp={}, coupons={:.2f})".format(
            self.esd, self.usdc, self.esds, self.eth, self.lp,
            sum(self.underlying_coupons.values()) + sum(self.premium_coupons.values()))
        
    def get_strategy(self, block, price, total_supply):
        """
        Get weights, as a dict from action to float, as a function of the price.
        """
        
        strategy = collections.defaultdict(lambda: 1.0)
        
        # TODO: real (learned? adversarial? GA?) model of the agents
        # TODO: agent preferences/utility function
        
        if price > 1.0:
            # Expansion so we want to bond
            strategy["bond"] = 2.0
            # Or redeem if possible
            strategy["redeem"] = 100
            
        if price * total_supply > self.get_faith(block, price, total_supply):
            # There is too much ESD, so we want to sell
            strategy["sell"] = 4.0
        else:
            # We prefer to buy
            strategy["buy"] = 4.0
        
        return strategy
        
    def get_faith(self, block, price, total_supply):
        """
        Get the total faith in ESD that this agent has, in USDC.
        
        If the market cap is over the faith, the agent thinks the system is
        over-valued. If the market cap is under the faith, the agent thinks the
        system is under-valued.
        """
        
        # TODO: model the real economy as bidding on utility in
        # mutually-beneficial exchanges conducted in ESD, for which a velocity
        # is needed, instead of an abstract faith?
        
        # TODO: different faith for different people
        
        # This should oscilate between 500k and 1m every 500 blocks
        faith = 750000.0 + 250000.0 * math.sin(block * (2 * math.pi / 500))
        
        return faith

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
    
    def esd_price(self):
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
        
        new_value = esd * self.esd_price() + usdc
        held_value = self.esd * self.esd_price() + self.usdc
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
        
        # Coupon underlying parts by expiration epoch
        self.underlying_coupon_supply = collections.defaultdict(float)
        # Coupon premium parts by expiration epoch
        self.premium_coupon_supply = collections.defaultdict(float)
        
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
        
    def get_coupon_rate(self):
        """
        Return the rate of return on coupons (as a percentage that is the
        premium), if the premium doesn't expire.
        """
        
        # TODO: reaql logic here
        
        if self.esd_supply > 0:
            return self.debt / self.esd_supply
        else:
            return 0
        
    def couponable(self, esd):
        """
        Return the amount of ESD that can be couponed, up to the given value.
        """
       
        if self.expanding:
            return 0
        else:
            return min(esd, self.debt)
       
    def coupon(self, esd):
        """
        Spend the given number of ESD on coupons.
        Returns (redeem_by, underlying_coupons, premium_coupons)
        """
        
        rate = self.get_coupon_rate()
        
        underlying_coupons = esd
        premium_coupons = esd * rate
        redeem_by = self.epoch + 90
        
        self.esd_supply = max(0, self.esd_supply - esd)
        self.debt = max(0, self.debt - esd)
        self.underlying_coupon_supply[redeem_by] += underlying_coupons
        self.premium_coupon_supply[redeem_by] += premium_coupons
        
        return (redeem_by, underlying_coupons, premium_coupons)
        
    def redeemable(self, redeem_by, underlying_coupons, premium_coupons):
        """
        Return the maximum (underlying, premium) coupons currently redeemable
        from those expiring at the given epoch, up to the given limits.
        
        Premium coupons will always be redeemed even if expired; they just
        redeem for no money.
        """
        
        # TODO: real redemption cap logic
        
        if self.expanding:
            return (underlying_coupons, premium_coupons)
        else:
            # Don't let people redeem anything when not expanding, even the
            # underlying.
            return (0.0, 0.0)
    
    def redeem(self, redeem_by, underlying_coupons, premium_coupons):
        """
        Redeem the given number of coupons.
        
        Pays out the underlying and premium in an expansion phase, or only the
        underlying otherwise, or if the coupons are expired.
        """
        
        # TODO: real redeem logic
        
        self.underlying_coupon_supply[redeem_by] = max(0, self.underlying_coupon_supply[redeem_by] - underlying_coupons)
        self.premium_coupon_supply[redeem_by] = max(0, self.premium_coupon_supply[redeem_by] - premium_coupons)
        
        if self.epoch <= redeem_by and self.expanding:
            esd = underlying_coupons + premium_coupons
        else:
            esd = underlying_coupons
            
        self.esd_supply += esd
            
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
        
        if uniswap.esd_price() >= 1.0:
            self.expanding = True
        else:
            self.expanding = False
            
        if self.expanding:
            new_esd = self.interest * self.esd
            self.esd += new_esd
            self.esd_supply += new_esd
            self.debt = 0
        else:
            # TODO: real debt model, debt cap
            self.debt += self.esd_supply * 0.01
        
        reward = 1000
        self.esd_supply += reward
        
        return reward
        
    # TODO: model LP rewards
    
    
def portion_dedusted(total, fraction):
    """
    Compute the amount of an asset to use, given that you have
    total and you don't want to leave behind dust.
    """
    
    if total - (fraction * total) <= 1:
        return total
    else:
        return fraction * total
        

def drop_zeroes(d):
    """
    Delete all items with zero value from the dict d, in place.
    """
    
    to_remove = [k for k, v in d.items() if v == 0]
    for k in to_remove:
        del d[k]
                        
                        
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
        
    def log(self, stream):
        """
        Log block, epoch, price, supply, and faith to the given stream as a TSV line.
        """
        
        stream.write('{}\t{}\t{:.2f}\t{:.2f}\t{:.2f}\n'.format(
            self.block, self.dao.epoch, self.uniswap.esd_price(), self.dao.esd_supply,
            self.get_overall_faith()))
       
    def get_overall_faith(self):
        """
        What target should the system be trying to hit in ESD market cap?
        """
        
        return self.agents[0].get_faith(self.block, self.uniswap.esd_price(), self.dao.esd_supply)
       
    def step(self):
        """
        Step the model by one block. Let all the agents act.
        
        Returns True if anyone could act.
        """
        
        self.block += 1
        
        print("Block {}, epoch {}, price {:.2f}, supply {:.2f}, faith: {:.2f}, bonded {:.2f}, liquidity {:.2f} ESD / {:.2f} USDC".format(
            self.block, self.dao.epoch, self.uniswap.esd_price(), self.dao.esd_supply,
            self.get_overall_faith(), self.dao.esd, self.uniswap.esd, self.uniswap.usdc))
        
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
            if a.esd > 0 and self.dao.couponable(a.esd) > 0:
                options.append("coupon")
            if len(a.underlying_coupons) > 0:
                # Get the oldest coupons
                redeem_by, underlying = next(iter(a.underlying_coupons.items()))
                premium = a.premium_coupons[redeem_by]
                (redeem_underlying, redeem_premium) = self.dao.redeemable(redeem_by, underlying, premium)
                if redeem_underlying > 0 or redeem_premium > 0:
                    options.append("redeem")
            if a.usdc > 0 and a.esd > 0:
                options.append("deposit")
            if a.lp > 0:
                options.append("withdraw")
                
            # TODO: coupons
                
            if len(options) > 0:
                # We can act
        
                strategy = a.get_strategy(self.block, self.uniswap.esd_price(), self.dao.esd_supply)
                
                weights = [strategy[o] for o in options]
                
                action = random.choices(options, weights=weights)[0]
                
                # What fraction of the total possible amount of doing this
                # action will the agent do?
                commitment = random.random() * 0.1
                
                print("Agent {}: {}".format(agent_num, action))
                
                if action == "buy":
                    usdc = portion_dedusted(a.usdc, commitment)
                    esd = self.uniswap.buy(usdc)
                    a.usdc -= usdc
                    a.esd += esd
                    print("Buy {:.2f} ESD for {:.2f} USDC".format(esd, usdc))
                elif action == "sell":
                    esd = portion_dedusted(a.esd, commitment)
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
                    esd = portion_dedusted(a.esd, commitment)
                    esds = self.dao.bond(esd)
                    a.esd -= esd
                    a.esds += esds
                    print("Bond {:.2f} ESD".format(esd))
                elif action == "unbond":
                    esds = portion_dedusted(a.esds, commitment)
                    esd = self.dao.unbond(esds)
                    a.esds -= esds
                    a.esd += esd
                    print("Unbond {:.2f} ESD".format(esd))
                elif action == "coupon":
                    esd = self.dao.couponable(portion_dedusted(a.esd, commitment))
                    (redeem_by, underlying_coupons, premium_coupons) = self.dao.coupon(esd)
                    a.esd = max(0, a.esd - esd)
                    a.underlying_coupons[redeem_by] += underlying_coupons
                    a.premium_coupons[redeem_by] += premium_coupons
                    print("Burn {:.2f} ESD for {:.2f} coupons".format(esd, underlying_coupons + premium_coupons))
                elif action == "redeem":
                    total_redeemed = 0
                    total_esd = 0
                    # We just redeem everything we can, in dict order, and ignore commitment
                    for redeem_by, underlying_coupons in a.underlying_coupons.items():
                        premium_coupons = a.premium_coupons[redeem_by]
                        
                        (underlying_redeemed, premium_redeemed) = self.dao.redeemable(redeem_by, underlying_coupons, premium_coupons)
                        esd = self.dao.redeem(redeem_by, underlying_redeemed, premium_redeemed)
                        
                        a.underlying_coupons[redeem_by] = max(0, a.underlying_coupons[redeem_by] - underlying_redeemed)
                        a.premium_coupons[redeem_by] = max(0, a.premium_coupons[redeem_by] - premium_redeemed)
                            
                        a.esd += esd
                        
                        total_esd += esd
                        total_redeemed += underlying_redeemed + premium_redeemed
                        
                    drop_zeroes(a.underlying_coupons)
                    drop_zeroes(a.premium_coupons)
                        
                    print("Redeem {:.2f} coupons for {:.2f} ESD".format(total_redeemed, total_esd))
                elif action == "deposit":
                    price = self.uniswap.esd_price()
                    
                    if a.esd * price < a.usdc:
                        esd = portion_dedusted(a.esd, commitment)
                        usdc = esd * price
                    else:
                        usdc = portion_dedusted(a.usdc, commitment)
                        esd = usdc / price
                    lp = self.uniswap.deposit(esd, usdc)
                    a.esd = max(0, a.esd - esd)
                    a.usdc = max(0, a.usdc - usdc)
                    a.lp += lp
                    print("Provide {:.2f} ESD and {:.2f} USDC".format(esd, usdc))
                elif action == "withdraw":
                    lp = portion_dedusted(a.lp, commitment)
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
    
    # Make a model of the economy
    model = Model()
    
    # Make a log file for system parameters, for analysis
    stream = open("log.tsv", "w")
    stream.write("#block\tepoch\tprice\tsupply\tfaith\n")
    
    for i in range(10000):
        # Every block
        # Try and tick the model
        if not model.step():
            # Nobody could act
            break
        # Log system state
        model.log(stream)
    
if __name__ == "__main__":
    main()
