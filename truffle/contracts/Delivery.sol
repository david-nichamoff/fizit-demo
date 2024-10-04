// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Delivery {

    address public owner;

    Contract[] contracts;                                   // [contract_idx]
    mapping (uint => Settlement[]) private settlements;     // contract_idx => settlement[]
    mapping (uint => Transaction[]) private transactions;   // contract_idx => transaction[]
    mapping (uint => Artifact[]) private artifacts;         // contract_idx => artifact_list[]
    mapping (uint => Party[]) private parties;              // contract_idx => party[]

    // every field ending in _dt is a unix timestamp
    // every field ending in _amt is an integer representing a float with 2 decimals
    // every field ending in _pct is an integer represending a float value with 4 decimals 
    // every field ending in _confirm is a string returned from the fiat payment provider

    struct Contract {
        string extended_data;           // json extended data
        string contract_name;           // description for display purposes
        string contract_type;           // the type of contract, e.g. ticketing, construction
        string funding_instr;           // buyer funding instructions
        uint service_fee_pct;           // service fee pct <= service_fee_max
        uint service_fee_max;           // maximum fee that can be charged if the rate is variable
        int service_fee_amt;            // flat rate amt if not percentage based
        uint advance_pct;               // amount of money that will be advanced to seller for every transaction
        uint late_fee_pct;              // an APR, daily rate calculated as late_fee_pct / 365
        string transact_logic;          // jsonlogic formula for calculating transaction amount
        int min_threshold;              // minimum expected amount for a deliverable (could be negative)
        int max_threshold;              // maximum expected amount for a deliverable
        string notes;                   // contract notes, can be used for additonal data requests
        bool is_active;                 // instead of deleting, clear this flag to False
        bool is_quote;                  // true if still in the quote stage
    }

    struct Settlement {
        string extended_data;           // json extended data
        uint settle_due_dt;             // date the payment is due 
        uint transact_min_dt;           // min date the transaction is made 
        uint transact_max_dt;           // max date the transaction is made 
        uint transact_count;            // number of transactions in this current settlement period 
        int advance_amt;                // the dollar amount that was advanced in this period (net amt)
        int advance_amt_gross;          // the dollar amount that was advanced in this period less fees
        uint settle_pay_dt;             // when the settlement was paid
        int settle_exp_amt;             // expected amount of settlement 0
        int settle_pay_amt;             // actual amount paid from the buyer
        string settle_confirm;          // confirmation from payment source
        int dispute_amt;                // if expected < actual, assume there was a dispute
        string dispute_reason;          // if dispute_amt > 0, what was the reason (if provided)
        uint days_late;                 // number of days late the payment was made
        int late_fee_amt;               // amount of the late fee, will be taken out of the residual
        uint residual_pay_dt;           // date and time the residual was paid
        int residual_pay_amt;           // will equal residual_calc_amt after payment intitiated
        string residual_confirm;        // residual confirmation from the payment source
        int residual_exp_amt;           // expected amount of the residual
        int residual_calc_amt;          // what the actual residual will be (exp - late_fee - dispute)
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
        string advance_confirm;         // payment confirmation of the advance from payment source
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
        address party_address;          // wallet address
        string party_type;              // the type of party associated with contract
    }

    event ContractEvent(uint indexed contract_idx, string eventType, string details);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Access denied, only contract owner can call this function");
        _;
    }

    function getContractCount() public view returns (uint) {
        return contracts.length;
    }

    function getContract(uint contract_idx) public view returns (Contract memory) {
        require(contract_idx < contracts.length, "Invalid contract index");
        return contracts[contract_idx];
    }

    function addContract (Contract memory contract_) public onlyOwner {
        contracts.push(contract_);
        emit ContractEvent(contracts.length - 1, "ContractAdded", contract_.contract_name);
    }

    function logContractChange(uint contract_idx, string memory field, string memory old_value, string memory new_value) private {
        if (keccak256(bytes(old_value)) != keccak256(bytes(new_value))) {
            emit ContractEvent(contract_idx, "ContractUpdated", string(abi.encodePacked(field, ":", old_value, "->", new_value)));
        }
    }

    function updateContract (uint contract_idx, Contract memory contract_) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        logContractChange(contract_idx, "extended_data", contracts[contract_idx].extended_data, contract_.extended_data);
        logContractChange(contract_idx, "contract_name", contracts[contract_idx].contract_name, contract_.contract_name);
        logContractChange(contract_idx, "contract_type", contracts[contract_idx].contract_type, contract_.contract_type);
        logContractChange(contract_idx, "funding_instr", contracts[contract_idx].funding_instr, contract_.funding_instr);
        logContractChange(contract_idx, "service_fee_pct", uintToString(contracts[contract_idx].service_fee_pct), uintToString(contract_.service_fee_pct));
        logContractChange(contract_idx, "service_fee_max", uintToString(contracts[contract_idx].service_fee_max), uintToString(contract_.service_fee_max));
        logContractChange(contract_idx, "service_fee_amt", intToString(contracts[contract_idx].service_fee_amt), intToString(contract_.service_fee_amt));
        logContractChange(contract_idx, "advance_pct", uintToString(contracts[contract_idx].advance_pct), uintToString(contract_.advance_pct));
        logContractChange(contract_idx, "late_fee_pct", uintToString(contracts[contract_idx].late_fee_pct), uintToString(contract_.late_fee_pct));
        logContractChange(contract_idx, "transact_logic", contracts[contract_idx].transact_logic, contract_.transact_logic);
        logContractChange(contract_idx, "notes", contracts[contract_idx].notes, contract_.notes);
        logContractChange(contract_idx, "is_active", boolToString(contracts[contract_idx].is_active), boolToString(contract_.is_active));
        logContractChange(contract_idx, "is_quote", boolToString(contracts[contract_idx].is_quote), boolToString(contract_.is_quote));
        contracts[contract_idx] = contract_;
    }

    // Mark a contract as inactive 
    function deleteContract(uint contract_idx) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        contracts[contract_idx].is_active = false;
        emit ContractEvent(contract_idx, "ContractDeleted", uintToString(contract_idx));
    }

    function getParties(uint contract_idx) public view returns (Party[] memory) {
        require(contract_idx < contracts.length, "Invalid contract index");
        return parties[contract_idx];
    }

    function addParty(uint contract_idx, Party memory party) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        parties[contract_idx].push(party);
        emit ContractEvent(contract_idx, "PartyAdded", party.party_code);
    }

    function deleteParty(uint contract_idx, uint party_idx) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        require(party_idx < parties[contract_idx].length, "Invalid party index");

        for (uint i = party_idx; i < parties[contract_idx].length - 1; i++) {
            parties[contract_idx][i] = parties[contract_idx][i + 1];
        }

        parties[contract_idx].pop();

        emit ContractEvent(contract_idx, "PartyDeleted", uintToString(party_idx));
    }

    function deleteParties(uint contract_idx) public onlyOwner {
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
        string memory s3_bucket, string memory s3_object_key, string memory s3_version_id) public onlyOwner {
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

    function deleteArtifact(uint contract_idx, uint artifact_idx) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        require(artifact_idx < artifacts[contract_idx].length, "Invalid artifact index");

        for (uint i = artifact_idx; i < artifacts[contract_idx].length - 1; i++) {
            artifacts[contract_idx][i] = artifacts[contract_idx][i + 1];
        }

        artifacts[contract_idx].pop();

        emit ContractEvent(contract_idx, "ArtifactDeleted", uintToString(artifact_idx));
    }

    function deleteArtifacts(uint contract_idx) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        delete artifacts[contract_idx];
        emit ContractEvent(contract_idx, "ArtifactsDeleted", "");
    }

    function getSettlements(uint contract_idx) public view returns (Settlement[] memory) {
        require(contract_idx < contracts.length, "Invalid contract index");
        return settlements[contract_idx];
    }

    function addSettlement(uint contract_idx, string memory extended_data, uint settle_due_dt, uint transact_min_dt, uint transact_max_dt) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        Settlement memory settlement;
        settlement.settle_due_dt = settle_due_dt;
        settlement.transact_min_dt = transact_min_dt;
        settlement.transact_max_dt = transact_max_dt;
        settlement.extended_data = extended_data;
        settlements[contract_idx].push(settlement);
        emit ContractEvent(contract_idx, "SettlementAdded", settlement.extended_data);
    }

    function deleteSettlements(uint contract_idx) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        delete settlements[contract_idx];
        emit ContractEvent(contract_idx, "SettlementsDeleted", "");
    }

    function getTransactions(uint contract_idx) public view returns (Transaction[] memory) {
        require(contract_idx < contracts.length, "Invalid contract index");
        return transactions[contract_idx];
    }

    function deleteTransactions(uint contract_idx) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        delete transactions[contract_idx];
        emit ContractEvent(contract_idx, "TransactionsDeleted", "");
    }

    function addTransaction(uint contract_idx, string memory extended_data, uint transact_dt, int transact_amt, string memory transact_data) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");

        Transaction memory transact;
        transact.extended_data = extended_data;
        transact.transact_dt = transact_dt;
        transact.transact_amt = transact_amt;
        transact.transact_data = transact_data;

        bool settle_found = false;
        int transact_advance_amt = 0;
        int transact_advance_amt_gross = 0;
        int service_fee_amt = 0;

        for (uint i = 0; i < settlements[contract_idx].length; i++) {
            Settlement storage settlement = settlements[contract_idx][i];
            // minimum date is inclusive, maximum date is exclusive
            if (transact_dt >= settlement.transact_min_dt && transact_dt < settlement.transact_max_dt) {
                if (transact_amt > 0) {
                    service_fee_amt = int((contracts[contract_idx].service_fee_pct * uint(transact_amt)) / 10000) + int(contracts[contract_idx].service_fee_amt);
                    transact_advance_amt_gross = int((uint(transact_amt) * contracts[contract_idx].advance_pct) / 10000);

                    // Determine the final advance amount after subtracting the service fee
                    if (transact_advance_amt_gross >= service_fee_amt) {
                        transact_advance_amt = transact_advance_amt_gross - service_fee_amt;
                    }
                }

                settlement.settle_exp_amt += transact_amt;
                settlement.advance_amt += transact_advance_amt;
                settlement.advance_amt_gross += transact_advance_amt_gross;
                settlement.residual_exp_amt = settlement.settle_exp_amt - settlement.advance_amt_gross;
                settlement.transact_count++;
                transact.advance_amt = transact_advance_amt;
                transact.service_fee_amt = service_fee_amt;
                settle_found = true;
            }
        }

        if (settle_found) {
            transactions[contract_idx].push(transact);
            emit ContractEvent(contract_idx, "TransactionAdded", transact.extended_data);
        } else {
            emit ContractEvent(contract_idx, "TransactionError", "No valid settlement period");
        }
    }

    function payAdvance(uint contract_idx, uint transact_idx, uint advance_pay_dt, uint advance_pay_amt, string memory advance_confirm) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        transactions[contract_idx][transact_idx].advance_pay_dt = advance_pay_dt;
        transactions[contract_idx][transact_idx].advance_pay_amt = advance_pay_amt;
        transactions[contract_idx][transact_idx].advance_confirm = advance_confirm;
        emit ContractEvent(contract_idx, "PayAdvance", "");
    }

    function postSettlement(uint contract_idx, uint settle_idx, uint settle_pay_dt, int settle_pay_amt, string memory settle_confirm, string memory dispute_reason) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        settlements[contract_idx][settle_idx].settle_pay_dt = settle_pay_dt;
        settlements[contract_idx][settle_idx].settle_pay_amt = settle_pay_amt;
        settlements[contract_idx][settle_idx].settle_confirm = settle_confirm;

        if (settle_pay_dt > settlements[contract_idx][settle_idx].settle_due_dt) {
            settlements[contract_idx][settle_idx].days_late = (settle_pay_dt - settlements[contract_idx][settle_idx].settle_due_dt) / 60 / 60 / 24;

            // Convert necessary values to int to match types and avoid errors
            int days_late = int(settlements[contract_idx][settle_idx].days_late);
            int late_fee_pct = int(contracts[contract_idx].late_fee_pct);
            int settle_exp_amt = settlements[contract_idx][settle_idx].settle_exp_amt;

            settlements[contract_idx][settle_idx].late_fee_amt = (days_late * ((late_fee_pct * 100000) / 365) * settle_exp_amt) / 1000000000;
        }

        if (settle_pay_amt < settlements[contract_idx][settle_idx].settle_exp_amt) {
            settlements[contract_idx][settle_idx].dispute_amt = settlements[contract_idx][settle_idx].settle_exp_amt - settle_pay_amt;
            settlements[contract_idx][settle_idx].dispute_reason = dispute_reason;
        } 

        if ((settlements[contract_idx][settle_idx].residual_exp_amt - settlements[contract_idx][settle_idx].late_fee_amt - settlements[contract_idx][settle_idx].dispute_amt) > 0) {
            settlements[contract_idx][settle_idx].residual_calc_amt = settlements[contract_idx][settle_idx].residual_exp_amt - settlements[contract_idx][settle_idx].late_fee_amt -
                settlements[contract_idx][settle_idx].dispute_amt;
        } else {
            settlements[contract_idx][settle_idx].residual_calc_amt = 0;
        }

        emit ContractEvent(contract_idx, "PostSettlement", "");
    }

    function payResidual(uint contract_idx, uint settle_idx, uint residual_pay_dt, int residual_pay_amt, string memory residual_confirm) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        settlements[contract_idx][settle_idx].residual_pay_dt = residual_pay_dt;
        settlements[contract_idx][settle_idx].residual_pay_amt = residual_pay_amt;
        settlements[contract_idx][settle_idx].residual_confirm = residual_confirm;
        emit ContractEvent(contract_idx, "ResidualPaid", "");
    }

    function importContract(Contract memory contract_) public onlyOwner {
        contracts.push(contract_);
    }

    function importParty(uint contract_idx, Party memory party) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        parties[contract_idx].push(party);
    }

    function importSettlement(uint contract_idx, Settlement memory settlement) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        settlements[contract_idx].push(settlement);
    }

    function importTransaction(uint contract_idx, Transaction memory transaction) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        transactions[contract_idx].push(transaction);
    }

    function importArtifact(uint contract_idx, Artifact memory artifact) public onlyOwner {
        require(contract_idx < contracts.length, "Invalid contract index");
        artifacts[contract_idx].push(artifact);
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