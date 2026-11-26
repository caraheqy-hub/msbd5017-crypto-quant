
 // SPDX-License-Identifier: MIT
pragma solidity ^0.8.34;

contract BacktestRegistry {

    // 每一条存证记录
    struct Record {
        bytes32 dataHash;
        address submitter;
        uint256 timestamp;
    }

    // 根据记录编号查找存证
    mapping(uint256 => Record) public records;

    // 当前记录总数
    uint256 public recordCount;

    // 记录上链时发出事件
    event BacktestAnchored(
        uint256 indexed recordId,
        bytes32 indexed dataHash,
        address indexed submitter,
        uint256 timestamp
    );

    // 提交一条新的回测记录
    function anchorBacktest(
        bytes32 dataHash
    ) external returns (uint256) {

        require(
            dataHash != bytes32(0),
            "Empty hash"
        );

        uint256 id = recordCount;
        recordCount++;

        records[id] = Record({
            dataHash: dataHash,
            submitter: msg.sender,
            timestamp: block.timestamp
        });

        emit BacktestAnchored(
            id,
            dataHash,
            msg.sender,
            block.timestamp
        );

        return id;
    }

    // 查询某条记录的哈希
    function getHash(
        uint256 recordId
    ) external view returns (bytes32) {

        require(
            recordId < recordCount,
            "Record not found"
        );

        return records[recordId].dataHash;
    }
}
