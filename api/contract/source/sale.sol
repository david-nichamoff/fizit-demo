// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Advance {

    address public owner;

    Contract[] contracts;                                   // [contract_idx]
    mapping (uint => Settlement[]) private settlements;        // contract_idx => settlement[]
    mapping (uint => Transaction[]) private transactions;   // contract_idx => transaction[]
    mapping (uint => Artifact[]) private artifacts;         // contract_idx => artifact_list[]
    mapping (uint => Party[]) private parties;              // contract_idx => party[]

    // every field ending in _dt is a unix timestamp
    // every field ending in _amt is an integer representing a float with 2 decimals
    // every field ending in _pct is an integer represending a float value with 4 decimals 

    struct Contract {
        string extended_data;           // json extended data
        string contract_name;           // description for display purposes
        string funding_instr;           // funding instructions for the client
        string deposit_instr;           // deposit instructions to receive funds from buyer
        uint service_fee_pct;           // service fee as a percentage of value
        int service_fee_amt;            // flat rate amt if not percentage based
        uint late_fee_pct;              // an APR, daily rate calculated as late_fee_pct / 365
        string transact_logic;          // jsonlogic formula for calculating transaction amount
        string notes;                   // contract notes, can be used for additonal data requests
        bool is_active;                 // instead of deleting, clear this flag to False
        bool is_quote;                  // true if still in the quote stage
    }

    struct Settlement {
        string extended_data;           // json extended data
        uint settle_due_dt;             // date the payment is due 
        uint settle_pay_dt;             // when the settlement was paid
        int settle_exp_amt;             // expected amount of settlement 
        int settle_pay_amt;             // actual amount paid from the buyer
        string settle_tx_hash;          // store proof of payment for delivery
        uint days_late;                 // number of days late the payment was made
        int late_fee_amt;               // amount of the late fee, will be taken out of client funding
        int principal_amt;              // amount funded up front
        uint dist_pay_dt;               // date and time the client was paid
        int dist_pay_amt;               // will equal client_calc_amt after payment intitiated
        int dist_calc_amt;              // what the actual payment to client will be (settle_pay_amt - service_fee_amt - principal_amt)
        string dist_tx_hash;            // store proof of distribution for client
    }

    struct Transaction {
        string extended_data;           // json extended data
        uint transact_dt;               // date and time of the transaction
        int transact_amt;               // calculated value of a transaction, negative if an adjustment
        string transact_data;           // data regarding transaction for jsonlogic    
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
        logContractChange(contract_idx, "deposit_instr", contracts[contract_idx].deposit_instr, contract_.deposit_instr);
        logContractChange(contract_idx, "service_fee_pct", uintToString(contracts[contract_idx].service_fee_pct), uintToString(contract_.service_fee_pct));
        logContractChange(contract_idx, "service_fee_amt", intToString(contracts[contract_idx].service_fee_amt), intToString(contract_.service_fee_amt));
        logContractChange(contract_idx, "late_fee_pct", uintToString(contracts[contract_idx].late_fee_pct), uintToString(contract_.late_fee_pct));
        logContractChange(contract_idx, "transact_logic", contracts[contract_idx].transact_logic, contract_.transact_logic);
        logContractChange(contract_idx, "notes", contracts[contract_idx].notes, contract_.notes);
        logContractChange(contract_idx, "is_active", boolToString(contracts[contract_idx].is_active), boolToString(contract_.is_active));
        logContractChange(contract_idx, "is_quote", boolToString(contracts[contract_idx].is_quote), boolToString(contract_.is_quote));
        contracts[contract_idx] = contract_;
    }

    // Mark a contract as inactive 
    function deleteContract(uint contract_idx) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        contracts[contract_idx].is_active = false;
        emit ContractEvent(contract_idx, "ContractDeleted", uintToString(contract_idx));
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

    function getSettlements(uint contract_idx) public view returns (Settlement[] memory) {
        require(contract_idx < contracts.length, "Invalid contract index");
        return settlements[contract_idx];
    }

    function addSettlement(uint contract_idx, string memory extended_data, uint settle_due_dt, int principal_amt, int settle_exp_amt) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        Settlement memory settlement;
        settlement.settle_due_dt = settle_due_dt;
        settlement.settle_exp_amt = settle_exp_amt;
        settlement.extended_data = extended_data;
        settlement.principal_amt = principal_amt;
        settlements[contract_idx].push(settlement);
        emit ContractEvent(contract_idx, "SettlementAdded", uintToString(settle_due_dt));
    }

    function deleteSettlements(uint contract_idx) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        delete settlements[contract_idx];
        emit ContractEvent(contract_idx, "SettlementsDeleted", "");
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
        transactions[contract_idx].push(transact);
        emit ContractEvent(contract_idx, "TransactionAdded", uintToString(transact.transact_dt));
    }

    function postSettlement(uint contract_idx, uint settle_idx, uint settle_pay_dt, int settle_pay_amt, string memory settle_tx_hash) public {
        require(contract_idx < contracts.length, "Invalid contract index");

        settlements[contract_idx][settle_idx].settle_pay_dt = settle_pay_dt;
        settlements[contract_idx][settle_idx].settle_pay_amt = settle_pay_amt;
        settlements[contract_idx][settle_idx].settle_tx_hash = settle_tx_hash;

        int settle_exp_amt = settlements[contract_idx][settle_idx].settle_exp_amt; 

        if (settle_pay_dt > settlements[contract_idx][settle_idx].settle_due_dt) {
            settlements[contract_idx][settle_idx].days_late = (settle_pay_dt - settlements[contract_idx][settle_idx].settle_due_dt) / 60 / 60 / 24;

            // Convert necessary values to int to match types and avoid errors
            int days_late = int(settlements[contract_idx][settle_idx].days_late);
            int late_fee_pct = int(contracts[contract_idx].late_fee_pct);
            settlements[contract_idx][settle_idx].late_fee_amt = (days_late * ((late_fee_pct * 100000) / 365) * settle_exp_amt) / 1000000000;
        }

        int service_fee_amt = int((contracts[contract_idx].service_fee_pct * uint(settle_exp_amt)) / 10000) + int(contracts[contract_idx].service_fee_amt);
        int late_fee_amt = settlements[contract_idx][settle_idx].late_fee_amt;
        int principal_amt = settlements[contract_idx][settle_idx].principal_amt;

        if (settle_pay_amt - late_fee_amt - principal_amt - service_fee_amt > 0) {
            settlements[contract_idx][settle_idx].dist_calc_amt = settle_pay_amt - late_fee_amt - principal_amt - service_fee_amt;
        } else {
            settlements[contract_idx][settle_idx].dist_calc_amt = 0;
        }

        emit ContractEvent(contract_idx, "SettlementPosted", "");
    }

    function payDistribution(uint contract_idx, uint settle_idx, uint dist_pay_dt, int dist_pay_amt, string memory dist_tx_hash) public {
        require(contract_idx < contracts.length, "Invalid contract index");
        settlements[contract_idx][settle_idx].dist_pay_dt = dist_pay_dt;
        settlements[contract_idx][settle_idx].dist_pay_amt = dist_pay_amt;
        settlements[contract_idx][settle_idx].dist_tx_hash = dist_tx_hash;
        emit ContractEvent(contract_idx, "DistributionPaid", "");
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