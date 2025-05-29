// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Purchase {

    address public owner;

    Contract[] contracts;                                   // [contract_idx]
    mapping (uint => Transaction[]) private transactions;   // contract_idx => transaction[]
    mapping (uint => Artifact[]) private artifacts;         // contract_idx => artifact_list[]
    mapping (uint => Party[]) private parties;              // contract_idx => party[]

    // every field ending in _dt is a unix timestamp
    // every field ending in _amt is an integer representing a float with 2 decimals
    // every field ending in _pct is an integer represending a float value with 4 decimals 

    struct Contract {
        string extended_data;           // json extended data
        string contract_name;           // description for display purposes
        string funding_instr;           // funding instructions
        uint service_fee_pct;           // service fee pct <= service_fee_max
        int service_fee_amt;            // flat rate amt if not percentage based
        string transact_logic;          // jsonlogic formula for calculating transaction amount
        string notes;                   // contract notes, can be used for additonal data requests
        bool is_active;                 // instead of deleting, clear this flag to False
    }

    struct Transaction {
        string extended_data;           // json extended data
        uint transact_dt;               // date and time of the transaction
        int transact_amt;               // calculated value of a transaction, negative if an adjustment
        int service_fee_amt;            // calculated fee for a transaction
        int advance_amt;                // advance_amt * advance_pct - service_fee_amt
        string transact_data;           // data regarding transaction for jsonlogic    
        uint advance_pay_dt;            // payment of advance
        uint advance_pay_amt;           // will equal advance amt after payment initiated
        string advance_tx_hash;         // used to store proof of payment for digital txn 
    }

    struct Artifact {
        string doc_title;               // Document title
        string doc_type;                // Document type (e.g., "application/pdf")
        uint added_dt;                  // Timestamp of when the artifact was added
        string s3_bucket;               // S3 bucket name
        string s3_object_key;           // S3 object key (full path to the document)
        string s3_version_id;           // S3 version ID for versioned objects
    }

    struct Party {
        string party_code;              // code associated with a party
        address party_addr;             // wallet address
        string party_type;              // the type of party associated with contract
        uint approved_dt;               // the date that the contract was approved
        string approved_user;           // the user id of the user that made the approval
    }

    event ContractEvent(uint indexed contract_idx, string eventType, string details);

    function getContractCount() public view returns (uint) {
        return contracts.length;
    }

    function getContract(uint contract_idx) public view returns (Contract memory) {
        require(contract_idx < contracts.length, "Invalid contract index");
        return contracts[contract_idx];
    }

    function addContract (Contract memory contract_) public {
        contracts.push(contract_);
        emit ContractEvent(contracts.length - 1, "ContractAdded", contract_.contract_name);
    }

    function logContractChange(uint contract_idx, string memory field, string memory old_value, string memory new_value) private {
        if (keccak256(bytes(old_value)) != keccak256(bytes(new_value))) {
            emit ContractEvent(contract_idx, "ContractUpdated", string(abi.encodePacked(field, ":", old_value, "->", new_value)));
        }
    }

    function updateContract (uint contract_idx, Contract memory contract_) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        logContractChange(contract_idx, "extended_data", contracts[contract_idx].extended_data, contract_.extended_data);
        logContractChange(contract_idx, "contract_name", contracts[contract_idx].contract_name, contract_.contract_name);
        logContractChange(contract_idx, "funding_instr", contracts[contract_idx].funding_instr, contract_.funding_instr);
        logContractChange(contract_idx, "service_fee_pct", uintToString(contracts[contract_idx].service_fee_pct), uintToString(contract_.service_fee_pct));
        logContractChange(contract_idx, "service_fee_amt", intToString(contracts[contract_idx].service_fee_amt), intToString(contract_.service_fee_amt));
        logContractChange(contract_idx, "transact_logic", contracts[contract_idx].transact_logic, contract_.transact_logic);
        logContractChange(contract_idx, "notes", contracts[contract_idx].notes, contract_.notes);
        logContractChange(contract_idx, "is_active", boolToString(contracts[contract_idx].is_active), boolToString(contract_.is_active));
        contracts[contract_idx] = contract_;
    }

    // Mark a contract as inactive 
    function deleteContract(uint contract_idx) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        contracts[contract_idx].is_active = false;
        emit ContractEvent(contract_idx, "ContractDeleted", uintToString(contract_idx));
    }

    // Mark a contract as active
    function activateContract(uint contract_idx) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        contracts[contract_idx].is_active = true;
        emit ContractEvent(contract_idx, "ContractActivated", "true");
    }

    function getParties(uint contract_idx) public view returns (Party[] memory) {
        require(contract_idx < contracts.length, "Invalid contract index");
        return parties[contract_idx];
    }

    function addParty(uint contract_idx, Party memory party) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        parties[contract_idx].push(party);
        emit ContractEvent(contract_idx, "PartyAdded", party.party_code);
    }

    function approveParty(uint contract_idx, uint party_idx, uint approved_dt, string memory approved_user) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        require(party_idx < parties[contract_idx].length, "Invalid party index");
        parties[contract_idx][party_idx].approved_dt = approved_dt;
        parties[contract_idx][party_idx].approved_user = approved_user;

        emit ContractEvent(contract_idx, "PartyApproved", parties[contract_idx][party_idx].party_code);
    }

    function deleteParties(uint contract_idx) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        delete parties[contract_idx];
        emit ContractEvent(contract_idx, "PartiesDeleted", "");
    }

    function getArtifacts(uint contract_idx) public view returns (Artifact[] memory) {
        require(contract_idx < contracts.length, "Invalid contract index");
        return artifacts[contract_idx];
    }

    // Update addArtifact function:
    function addArtifact(uint contract_idx, string memory doc_title, string memory doc_type, uint added_dt,
        string memory s3_bucket, string memory s3_object_key, string memory s3_version_id) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        Artifact memory artifact;
        artifact.doc_title = doc_title;
        artifact.doc_type = doc_type;
        artifact.added_dt = added_dt;
        artifact.s3_bucket = s3_bucket;
        artifact.s3_object_key = s3_object_key;
        artifact.s3_version_id = s3_version_id;
        artifacts[contract_idx].push(artifact);
        emit ContractEvent(contract_idx, "ArtifactAdded", doc_title);
    }

    function deleteArtifacts(uint contract_idx) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        delete artifacts[contract_idx];
        emit ContractEvent(contract_idx, "ArtifactsDeleted", "");
    }

    function getTransactions(uint contract_idx) public view returns (Transaction[] memory) {
        require(contract_idx < contracts.length, "Invalid contract index");
        return transactions[contract_idx];
    }

    function deleteTransactions(uint contract_idx) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        delete transactions[contract_idx];
        emit ContractEvent(contract_idx, "TransactionsDeleted", "");
    }

    function addTransaction(uint contract_idx, string memory extended_data, uint transact_dt, int transact_amt, string memory transact_data) public {
        require(contract_idx < contracts.length, "Invalid contract index");

        Transaction memory transact;
        transact.extended_data = extended_data;
        transact.transact_dt = transact_dt;
        transact.transact_amt = transact_amt;
        transact.transact_data = transact_data;
        transact.service_fee_amt = int((contracts[contract_idx].service_fee_pct * uint(transact_amt)) / 10000) + int(contracts[contract_idx].service_fee_amt);
        transact.advance_amt = transact.transact_amt - transact.service_fee_amt;
        transactions[contract_idx].push(transact);
        emit ContractEvent(contract_idx, "TransactionAdded", uintToString(transact.transact_dt));
    }

    function payAdvance(uint contract_idx, uint transact_idx, uint advance_pay_dt, uint advance_pay_amt, string memory advance_tx_hash) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        require(transact_idx < transactions[contract_idx].length, "Invalid transaction index");
        transactions[contract_idx][transact_idx].advance_pay_dt = advance_pay_dt;
        transactions[contract_idx][transact_idx].advance_pay_amt = advance_pay_amt;
        transactions[contract_idx][transact_idx].advance_tx_hash = advance_tx_hash;
        emit ContractEvent(contract_idx, "AdvancePaid", "");
    }

    function uintToString(uint v) internal pure returns (string memory) {
        if (v == 0) {
            return "0";
        }
        uint j = v;
        uint len;
        while (j != 0) {
            len++;
            j /= 10;
        }
        bytes memory bstr = new bytes(len);
        uint k = len;
        while (v != 0) {
            k = k - 1;
            uint8 temp = (48 + uint8(v - v / 10 * 10));
            bytes1 b1 = bytes1(temp);
            bstr[k] = b1;
            v /= 10;
        }
        return string(bstr);
    }

   function intToString(int v) internal pure returns (string memory) {
        if (v == 0) {
            return "0";
        }

        bool negative = v < 0;
        uint len = 0;
        uint i;
        int temp = v;

        if (negative) {
            temp = -temp;
            len++;
        }

        i = uint(temp);

        while (i != 0) {
            len++;
            i /= 10;
        }

        bytes memory bstr = new bytes(len);
        uint k = len;
        i = uint(temp);

        while (i != 0) {
            k = k - 1;
            uint8 tempDigit = (48 + uint8(i - i / 10 * 10));
            bytes1 b1 = bytes1(tempDigit);
            bstr[k] = b1;
            i /= 10;
        }

        if (negative) {
            bstr[0] = '-';
        }

        return string(bstr);
    } 

    function boolToString(bool v) internal pure returns (string memory) {
        return v ? "true" : "false";
    }
}