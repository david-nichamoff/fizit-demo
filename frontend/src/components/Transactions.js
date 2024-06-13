import React, { useState, useEffect } from 'react';
import { formatCurrency, formatDateTime } from './Utils';
import axios from 'axios';
import './Transactions.css';

const Transactions = ({ contractIdx }) => {
  const [transactions, setTransactions] = useState([]);
  const [selectedTransaction, setSelectedTransaction] = useState(null);

  useEffect(() => {
    axios.get(`/api/contracts/${contractIdx}/transactions`)
      .then(response => setTransactions(response.data))
      .catch(error => console.error(`Error fetching transactions for contract ${contractIdx}:`, error));
  }, [contractIdx]);

  const handleTransactionSelect = (transaction) => {
    setSelectedTransaction(transaction);
  };

  return (
    <div className="transactions-container">
      <h2>Transactions</h2>
      <div className="transaction-header">
        <div className="column-header string-column">Contract</div>
        <div className="column-header time-column">Date</div>
        <div className="column-header amount-column">Amount</div>
        <div className="column-header amount-column">Advanced</div>
      </div>
      <ul className="transaction-list">
        {transactions.map((transaction, index) => (
          <li 
            key={index} 
            className={`transaction-item ${transaction === selectedTransaction ? 'selected' : ''}`}
            onClick={() => handleTransactionSelect(transaction)}
          >
            <div className="transaction-column string-column">{transaction.contract_name}</div>
            <div className="transaction-column time-column">{formatDateTime(transaction.transact_dt)}</div>
            <div className="transaction-column amount-column">{formatCurrency(transaction.transact_amt)}</div>
            <div className="transaction-column amount-column">{formatCurrency(transaction.advance_pay_amt)}</div>
          </li>
        ))}
      </ul>
      {selectedTransaction && (
        <div className="transaction-detail">
          <h3>Transaction Details</h3>
          <p>Contract: {selectedTransaction.contract_name}</p>
          <p>Date: {formatDateTime(selectedTransaction.transact_dt)}</p>
          <p>Amount: {formatCurrency(selectedTransaction.transact_amt)}</p>
          <p>Advanced: {formatCurrency(selectedTransaction.advance_pay_amt)}</p>
        </div>
      )}
    </div>
  );
};

export default Transactions;