import React from 'react';
import { formatCurrency, formatDateTime } from './Utils';
import './TransactionDetail.css';

const formatJsonAsGrid = (jsonObject) => {
  return (
    <>
      {Object.entries(jsonObject).map(([key, value], index) => (
        <React.Fragment key={index}>
          <div className="json-key">{key}</div>
          <div className="json-value">{JSON.stringify(value)}</div>
        </React.Fragment>
      ))}
    </>
  );
};

const TransactionDetail = ({ transaction }) => {
  const isTransactionSelected = !!transaction;

  return (
    <div className="transaction-detail-container">
      <h2>Transaction Details</h2>
      <div className="transaction-grid">
        <div className="header-row">Transaction Details</div>
        <div className="json-key">Contract Name</div>
        <div className="json-value">{isTransactionSelected ? transaction.contract_name : ''}</div>
        <div className="json-key">Transaction Date</div>
        <div className="json-value">{isTransactionSelected ? formatDateTime(transaction.transact_dt) : ''}</div>
        <div className="json-key">Transaction Amount</div>
        <div className="json-value">{isTransactionSelected ? formatCurrency(transaction.transact_amt) : ''}</div>
        
        <div className="header-row">Advance Details</div>
        <div className="json-key">Amount Advanced</div>
        <div className="json-value">{isTransactionSelected ? formatCurrency(transaction.advance_pay_amt) : ''}</div>
        <div className="json-key">Advanced Date</div>
        <div className="json-value">{isTransactionSelected ? formatDateTime(transaction.advance_pay_dt) : ''}</div>

        <div className="header-row">Identifiers</div>
        {isTransactionSelected ? formatJsonAsGrid(transaction.extended_data) : null}

        <div className="header-row">Transaction Data</div>
        {isTransactionSelected ? formatJsonAsGrid(transaction.transact_data) : null}
      </div>
    </div>
  );
};

export default TransactionDetail;