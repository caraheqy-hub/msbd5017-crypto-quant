// SPDX-License-Identifier: MIT
pragma solidity ^0.8.34;
import {Test} from "forge-std/Test.sol";
import {BacktestRegistry} from "./BacktestRegistry.sol";
contract BacktestRegistryTest is Test {
    BacktestRegistry registry;
    event BacktestAnchored(uint256 indexed recordId, bytes32 indexed dataHash, address indexed submitter, uint256 timestamp);
    function setUp() public { registry = new BacktestRegistry(); }
    function test_EmptyRegistry() public view { assertEq(registry.recordCount(), 0); }
    function test_RejectEmptyHash() public {
        vm.expectRevert(bytes("Empty hash"));
        registry.anchorBacktest(bytes32(0));
    }
    function test_RejectMissingRecord() public {
        vm.expectRevert(bytes("Record not found"));
        registry.getHash(0);
    }
    function test_RecordsAreAppendOnly() public {
        registry.anchorBacktest(bytes32(uint256(1)));
        registry.anchorBacktest(bytes32(uint256(2)));
        assertEq(registry.recordCount(), 2);
        assertEq(registry.getHash(0), bytes32(uint256(1)));
        assertEq(registry.getHash(1), bytes32(uint256(2)));
    }
    function testFuzz_StoreHashAndMetadata(bytes32 dataHash, address user) public {
        vm.assume(dataHash != bytes32(0));
        vm.expectEmit(true, true, true, true);
        emit BacktestAnchored(0, dataHash, user, block.timestamp);
        vm.prank(user);
        assertEq(registry.anchorBacktest(dataHash), 0);
        (bytes32 stored, address submitter, uint256 timestamp) = registry.records(0);
        assertEq(stored, dataHash);
        assertEq(submitter, user);
        assertEq(timestamp, block.timestamp);
    }
}
