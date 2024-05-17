import React from 'react';
import { formatCurrency, formatDateTime } from './Utils';
import './TransactionDetail.css';

const TransactionDetail = ({ transaction }) => {
  const isTransactionSelected = !!transaction;

  return (
    <div className="transaction-detail-container">
      <h2>Transaction Details</h2>
      {isTransactionSelected ? (
        <>
          <p><strong>Contract:</strong> {transaction.contract_name}</p>
          <p><strong>Transaction Date:</strong> {formatDateTime(transaction.transact_dt)}</p>
          <p><strong>Transaction Amount:</strong> {formatCurrency(transaction.transact_amt)}</p>
          <p><strong>Amount Advanced:</strong> {formatCurrency(transaction.advance_pay_amt)}</p>
          <p><strong>Advanced Date:</strong> {formatDateTime(transaction.advance_pay_dt)}</p>
          <p><strong>External Identifiers:</strong> {JSON.stringify(transaction.ext_id)}</p>
          <p><strong>Transaction Data:</strong> {JSON.stringify(transaction.transact_data)}</p>
        </>
      ) : (
        <>
          <p><strong>Contract:</strong></p>
          <p><strong>Transaction Date:</strong></p>
          <p><strong>Transaction Amount:</strong></p>
          <p><strong>Amount Advanced:</strong></p>
          <p><strong>Advanced Date:</strong></p>
          <p><strong>External Identifiers:</strong></p>
          <p><strong>Transaction Data:</strong></p>
        </>
      )}
    </div>
  );
};

export default TransactionDetail;
