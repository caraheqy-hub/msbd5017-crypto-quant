// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @notice Publishes a digest of an off-chain backtest artifact. The data itself stays off-chain.
contract BacktestAnchor {
    mapping(bytes32 => address) public publisher;

    event Anchored(bytes32 indexed root, address indexed author, string uri);

    function anchor(bytes32 root, string calldata uri) external {
        require(root != bytes32(0), "empty root");
        require(publisher[root] == address(0), "already anchored");
        publisher[root] = msg.sender;
        emit Anchored(root, msg.sender, uri);
    }
}
