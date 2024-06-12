import React, { useState, useEffect } from 'react';
import Pagination from './Pagination';
import { formatCurrency, formatDateTime, formatDate } from './Utils';
import axios from 'axios';
import './PaymentsPage.css';

const PaymentsPage = ({ accounts, transactions, settlements }) => {
  const itemsPerPage = 12;
  const [filteredTransactions, setFilteredTransactions] = useState([]);
  const [filteredSettlements, setFilteredSettlements] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [selectedAccountId, setSelectedAccountId] = useState(null);
  const [selectedSettlementPeriod, setSelectedSettlementPeriod] = useState(null);
  const [currentPageTransactions, setCurrentPageTransactions] = useState(1);
  const [currentPageSettlements, setCurrentPageSettlements] = useState(1);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  useEffect(() => {
    setIsInitialLoad(false);
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      const today = new Date();
      const filteredTrans = transactions.filter(transaction => 
        transaction.funding_instr.account_id === selectedAccount.account_id && 
        transaction.advance_pay_amt === 0 &&
        new Date(transaction.transact_dt) <= today
      );
      setFilteredTransactions(filteredTrans);

      const filteredSett = settlements.filter(settlement => 
        settlement.funding_instr.account_id === selectedAccount.account_id &&
        settlement.residual_calc_amt > 0
      );
      setFilteredSettlements(filteredSett);
    }
  }, [selectedAccount, transactions, settlements]);

  const totalPagesTransactions = Math.ceil(filteredTransactions.length / itemsPerPage);
  const startIndexTransactions = (currentPageTransactions - 1) * itemsPerPage;
  const endIndexTransactions = Math.min(startIndexTransactions + itemsPerPage, filteredTransactions.length);
  const visibleTransactions = filteredTransactions.slice(startIndexTransactions, endIndexTransactions);

  const totalPagesSettlements = Math.ceil(filteredSettlements.length / itemsPerPage);
  const startIndexSettlements = (currentPageSettlements - 1) * itemsPerPage;
  const endIndexSettlements = Math.min(startIndexSettlements + itemsPerPage, filteredSettlements.length);
  const visibleSettlements = filteredSettlements.slice(startIndexSettlements, endIndexSettlements);

  const handlePageChangeTransactions = (page) => {
    setCurrentPageTransactions(page);
  };

  const handlePageChangeSettlements = (page) => {
    setCurrentPageSettlements(page);
  };

  const handleAccountSelect = (account) => {
    setSelectedAccount(account);
    setSelectedAccountId(account.account_id);
    setSelectedSettlementPeriod(null); 
  };

  const handlePayAdvance = async () => {
    try {
      await axios.post(`${process.env.REACT_APP_API_URL}/api/accounts/${selectedAccountId}/pay_advance`);
      alert('Advance payment successfully processed.');
    } catch (error) {
      console.error('Error processing advance payment:', error);
      alert('Failed to process advance payment.');
    }
  };

  const handlePayResidual = async () => {
    try {
      await axios.post(`${process.env.REACT_APP_API_URL}/api/accounts/${selectedAccountId}/pay_residual`);
      alert('Residual payment successfully processed.');
    } catch (error) {
      console.error('Error processing residual payment:', error);
      alert('Failed to process residual payment.');
    }
  };

  const transactionTotal = filteredTransactions.reduce((total, transaction) => total + transaction.advance_amt, 0);
  const settlementTotal = filteredSettlements.reduce((total, settlement) => total + settlement.residual_calc_amt, 0);

  return (
    <div className="detail-page">
      <div className="account-container">
        <h2>Accounts</h2>
        <div className="account-header">
          <div className="column-header shortstring-column">Bank</div>
          <div className="column-header string-column">Account Name</div>
          <div className="column-header amount-column">Balance</div>
        </div>
        <ul className="account-list">
          {accounts.map((account, index) => (
            <li 
              key={index} 
              className={`account-item ${account === selectedAccount ? 'selected' : ''}`}
              onClick={() => handleAccountSelect(account)}
            >
              <div className="account-column shortstring-column">{account.bank}</div>
              <div className="account-column string-column">{account.account_name}</div>
              <div className="account-column amount-column">{formatCurrency(account.available_balance)}</div>
            </li>
          ))}
        </ul>
      </div>
      {selectedAccount && (
        <div className="transaction-container">
          <h2>Transactions</h2>
          <div className="transaction-header">
            <div className="column-header string-column">Contract</div>
            <div className="column-header date-column">Date</div>
            <div className="column-header amount-column">Amount</div>
            <div className="column-header amount-column">Advance</div>
          </div>
          <ul className="transaction-list">
            {visibleTransactions.map((transaction, index) => (
              <li 
                key={index} 
                className={`transaction-item ${transaction === selectedAccount ? 'selected' : ''}`}
              >
                <div className="transaction-column string-column">{transaction.contract_name}</div>
                <div className="transaction-column date-column">{formatDateTime(transaction.transact_dt)}</div>
                <div className="transaction-column amount-column">{formatCurrency(transaction.transact_amt)}</div>
                <div className="transaction-column amount-column">{formatCurrency(transaction.advance_amt)}</div>
              </li>
            ))}
          </ul>
          <div className="transaction-footer">
            <div className="column-footer">
              Total: {formatCurrency(transactionTotal)}
            </div>
            <button 
              className="pay-button"
              onClick={handlePayAdvance} 
              disabled={filteredTransactions.length === 0}
            >
              Pay Advance
            </button>
          </div>
          <Pagination currentPage={currentPageTransactions} totalPages={totalPagesTransactions} onPageChange={handlePageChangeTransactions} />
        </div>
      )}
      {selectedAccount && (
        <div className="settlement-container">
          <h2>Settlements</h2>
          <div className="settlement-header">
            <div className="column-header string-column">Contract</div>
            <div className="column-header date-column">Settle Due Date</div>
            <div className="column-header amount-column">Residual Calc Amt</div>
          </div>
          <ul className="settlement-list">
            {visibleSettlements.map((settlement, index) => (
              <li 
                key={index} 
                className={`settlement-item ${settlement === selectedSettlementPeriod ? 'selected' : ''}`}
                onClick={() => setSelectedSettlementPeriod(settlement)}
              >
                <div className="settlement-column string-column">{settlement.contract_name}</div>
                <div className="settlement-column date-column">{formatDate(settlement.settle_due_dt)}</div>
                <div className="settlement-column amount-column">{formatCurrency(settlement.residual_calc_amt)}</div>
              </li>
            ))}
          </ul>
          <div className="settlement-footer">
            <div className="column-footer">
              Total: {formatCurrency(settlementTotal)}
            </div>
            <button 
              className="pay-button"
              onClick={handlePayResidual} 
              disabled={filteredSettlements.length === 0}
            >
              Pay Residual
            </button>
          </div>
          <Pagination currentPage={currentPageSettlements} totalPages={totalPagesSettlements} onPageChange={handlePageChangeSettlements} />
        </div>
      )}
    </div>
  );
};

export default PaymentsPage;