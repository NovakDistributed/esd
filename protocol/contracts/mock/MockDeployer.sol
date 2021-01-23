/*
    Copyright 2020 Empty Set Squad <emptysetsquad@protonmail.com>

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
*/

pragma solidity ^0.5.17;
pragma experimental ABIEncoderV2;

import "../external/Decimal.sol";
import "../token/Dollar.sol";
import "./MockOracle.sol";
import "./MockPool.sol";
import "../dao/Upgradeable.sol";
import "../dao/Permission.sol";

import '@uniswap/v2-core/contracts/interfaces/IUniswapV2Factory.sol';


contract MockDeployer1 is State, Permission, Upgradeable {
    function initialize() initializer public {
        _state.provider.dollar = new Dollar();
    }

    function implement(address implementation) external {
        upgradeTo(implementation);
    }
}

contract MockDeployer2 is State, Permission, Upgradeable {
    function initialize() initializer public {
        // Make an oracle with no info in it except the dollar. We can call
        // set() on it from a contract that actually can have state, or from a
        // deployment, to fill in the other fields
        _state.provider.oracle = new MockOracle(address(0), address(dollar()), address(0));
        // And don't do oracle setup
    }

    function implement(address implementation) external {
        upgradeTo(implementation);
    }
}

contract MockDeployer3 is State, Permission, Upgradeable {
    
    function initialize() initializer public {
        MockOracle oracle = MockOracle(address(_state.provider.oracle));
        // Start off the pool with the USDC address we snuck in through the Oracle
        MockPool pool = new MockPool(oracle.getUsdc());
        _state.provider.pool = address(pool);
    }

    function implement(address implementation) external {
        upgradeTo(implementation);
    }
}
