// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Delivery {

    address public owner;
    
    Contract[] contracts;                                   // [contract_idx]
    mapping (uint => Settlement[]) private settlements;     // contract_idx => settlement[]
    mapping (uint => Transaction[]) private transactions;   // contract_idx => transaction[]
    mapping (uint => string[]) private artifacts;           // contract_idx => artifact_list[]

    // every field ending in _dt is a unix timestamp
    // every field ending in _amt is an integer representing a float with 2 decimals
    // every field ending in _pct is an integer represending a float value with 4 decimals 
    // every field ending in _confirm is a string returned from the fiat payment provider

    struct Contract {
        string ext_id;                  // json with list of external_id(s) for contract
        string contract_name;           // non-unique, description for display purposes
        string payment_instr;           // seller payment instructions
        string funding_instr;           // buyer funding instructions
        uint service_fee_pct;           // service fee can include a pct + flat rate amt
        uint service_fee_amt;           
        uint advance_pct;               // amount of money that will be advanced to seller for every transaction
        uint late_fee_pct;              // an APR, daily rate calculated as late_fee_pct / 365
        string transact_logic;          // jsonlogic formula for calculating transaction amount
        bool is_active;                 // instead of deleting, clear this flag to False
    }    

    struct Settlement {
        string ext_id;                  // json with list of external_id(s), e.g. invoice_id
        uint settle_due_dt;             // date the payment is due (midnight)   
        uint transact_min_dt;           // min date the transaction is made (midnight)
        uint transact_max_dt;           // max date the transaction is made (midnight) 
        uint transact_count; 
        uint settle_pay_dt;
        uint settle_exp_amt;            // expected amount of settlement
        uint settle_pay_amt;            // actual amount paid from the buyer
        string settle_confirm;
        uint dispute_amt;               // if expected  < actual, assume there was a dispute
        string dispute_reason;
        uint days_late; 
        uint late_fee_amt;              // amount of the late fee, will be taken out of the residual
        uint residual_pay_dt;
        uint residual_pay_amt;          // will equal residual_calc_amt after payment intitiated
        string residual_confirm;
        uint residual_exp_amt;          // expected amount of the residual
        uint residual_calc_amt;         // what the actual residual will be (exp - late_fee - dispute)
    }

    struct Transaction {
        string ext_id;                  // json external identifier for transaction
        uint transact_dt;               
        uint transact_amt;              // calculated value of a transaction of transaction
        uint advance_amt;               // advance_amt * advance_pct - service_fee_amt
        string transact_data;           // data regarding transaction for jsonlogic    
        uint advance_pay_dt;            // paymet of advance
        uint advance_pay_amt;           // will equal advance amt after payment initiated
        string advance_confirm;
    }

    event ContractAdded(uint indexed contract_idx);
    event ContractUpdated(uint indexed contract_idx);
    event TransactionAdded(uint indexed contract_idx, uint indexed transact_idx);
    event ArtifactAdded(uint indexed contract_idx, uint indexed artifact_idx);
    event SettlementAdded(uint indexed contract_idx, uint indexed settle_idx);
    event AdvancePaid(uint indexed contract_idx, uint indexed transact_idx);
    event SettlementPosted(uint indexed contract_idx, uint indexed settle_idx);
    event ResidualPaid(uint indexed contract_idx, uint indexed settle_idx);

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
        return contracts[contract_idx];
    }

    function addContract (Contract memory contract_) public onlyOwner {
        contracts.push(contract_);
        emit ContractAdded(contracts.length - 1);
    }

    function updateContract (uint contract_idx, Contract memory contract_) public onlyOwner {
        contracts[contract_idx] = contract_;
        emit ContractUpdated(contract_idx);
    }

    function getArtifacts (uint contract_idx) public view returns (string[] memory) {
        return artifacts[contract_idx];
    }

    function addArtifact (uint contract_idx, string memory artifact_id) public onlyOwner {
        artifacts[contract_idx].push(artifact_id);
        emit ArtifactAdded(contract_idx, artifacts[contract_idx].length - 1);
    }

    function deleteArtifacts(uint contract_idx) public onlyOwner {
        delete artifacts[contract_idx];
    }

    function getSettlements(uint contract_idx) public view returns (Settlement[] memory) {
        return settlements[contract_idx];
    }

    function getSettlement(uint contract_idx, uint settle_idx) public view returns (Settlement memory) {
        return settlements[contract_idx][settle_idx];
    }

    function addSettlement(uint contract_idx, string memory ext_id, uint settle_due_dt, uint transact_min_dt, uint transact_max_dt) public onlyOwner {
        Settlement memory settlement;
        settlement.settle_due_dt = settle_due_dt;
        settlement.transact_min_dt = transact_min_dt;
        settlement.transact_max_dt = transact_max_dt;
        settlement.ext_id = ext_id;
        settlements[contract_idx].push(settlement);
        emit SettlementAdded(contract_idx, settlements[contract_idx].length - 1);
    }

    function deleteSettlements(uint contract_idx) public onlyOwner {
        require (contract_idx < contracts.length, "Invalid contract index");
        delete settlements[contract_idx];
    }

    function getTransactions(uint contract_idx) public view returns (Transaction[] memory) {
        return transactions[contract_idx];
    }

    function getTransaction(uint contract_idx, uint transact_idx) public view returns (Transaction memory) {
        return transactions[contract_idx][transact_idx];
    }

    function addTransaction(uint contract_idx, string memory ext_id, uint transact_dt, uint transact_amt, string memory transact_data) public onlyOwner {

        Transaction memory transact;
        transact.ext_id = ext_id;
        transact.transact_dt = transact_dt;
        transact.transact_amt = transact_amt;
        transact.transact_data = transact_data;

        for (uint i = 0; i < settlements[contract_idx].length; i++) {
            if (transact_dt >= settlements[contract_idx][i].transact_min_dt && transact_dt < settlements[contract_idx][i].transact_max_dt) {
                settlements[contract_idx][i].transact_count ++;
                settlements[contract_idx][i].settle_exp_amt += transact.transact_amt;
                settlements[contract_idx][i].residual_exp_amt += transact_amt - (transact_amt * contracts[contract_idx].advance_pct / 10000);
            }
        }

        uint service_fee = (contracts[contract_idx].service_fee_pct * transact_amt / 10000) + contracts[contract_idx].service_fee_amt;
        transact.advance_amt = (transact_amt * contracts[contract_idx].advance_pct / 10000) - service_fee;
        transactions[contract_idx].push(transact);
        emit TransactionAdded(contract_idx, transactions[contract_idx].length - 1);
    }

    function deleteTransactions(uint contract_idx) public onlyOwner {
        require (contract_idx < contracts.length, "Invalid contract index");
        delete transactions[contract_idx];
    }

    function payAdvance(uint contract_idx, uint transact_idx, uint advance_pay_dt, uint advance_pay_amt, string memory advance_confirm) public onlyOwner {
        transactions[contract_idx][transact_idx].advance_pay_dt = advance_pay_dt;
        transactions[contract_idx][transact_idx].advance_pay_amt = advance_pay_amt;
        transactions[contract_idx][transact_idx].advance_confirm = advance_confirm;
        emit AdvancePaid(contract_idx, transact_idx);
    }

    function postSettlement(uint contract_idx, uint settle_idx, uint settle_pay_dt, uint settle_pay_amt, string memory settle_confirm, string memory dispute_reason) public onlyOwner {
        settlements[contract_idx][settle_idx].settle_pay_dt = settle_pay_dt;
        settlements[contract_idx][settle_idx].settle_pay_amt = settle_pay_amt;
        settlements[contract_idx][settle_idx].settle_confirm = settle_confirm;

        if (settle_pay_dt > settlements[contract_idx][settle_idx].settle_due_dt) {
            settlements[contract_idx][settle_idx].days_late = (settle_pay_dt - settlements[contract_idx][settle_idx].settle_due_dt) / 60 / 60 / 24;
            settlements[contract_idx][settle_idx].late_fee_amt = (settlements[contract_idx][settle_idx].days_late * 
                ((contracts[contract_idx].late_fee_pct * 100000) / 365) * settlements[contract_idx][settle_idx].settle_exp_amt) / 1000000000;
        }

        if (settle_pay_amt < settlements[contract_idx][settle_idx].residual_exp_amt) {
            settlements[contract_idx][settle_idx].dispute_amt = settle_pay_amt - settlements[contract_idx][settle_idx].residual_exp_amt;
            settlements[contract_idx][settle_idx].dispute_reason = dispute_reason;
        } 
        
        if ((settlements[contract_idx][settle_idx].residual_exp_amt - settlements[contract_idx][settle_idx].late_fee_amt - settlements[contract_idx][settle_idx].dispute_amt) > 0) {
            settlements[contract_idx][settle_idx].residual_calc_amt = settlements[contract_idx][settle_idx].residual_exp_amt - settlements[contract_idx][settle_idx].late_fee_amt -
                settlements[contract_idx][settle_idx].dispute_amt;
        } 
        emit SettlementPosted(contract_idx, settle_idx);
    }

    function payResidual(uint contract_idx, uint settle_idx, uint residual_pay_dt, uint residual_pay_amt, string memory residual_confirm) public onlyOwner {
        settlements[contract_idx][settle_idx].residual_pay_dt = residual_pay_dt;
        settlements[contract_idx][settle_idx].residual_pay_amt = residual_pay_amt;
        settlements[contract_idx][settle_idx].residual_confirm = residual_confirm;
        emit ResidualPaid(contract_idx, settle_idx);
    }
}