import React from 'react';
import { formatCurrency, formatDate } from './Utils';
import './SettlementDetail.css';

const SettlementDetail = ({ settlement }) => {
  const isSettlementSelected = !!settlement;

  return (
    <div className="settlement-detail-container">
      <h2>Settlement Details</h2>
      {isSettlementSelected ? (
        <>
          <p><strong>Contract:</strong> {settlement.contract_name}</p>
          <p><strong>Due Date:</strong> {formatDate(settlement.settle_due_dt)}</p>
          <p><strong>Transaction Start Date:</strong> {formatDate(settlement.transact_min_dt)}</p>
          <p><strong>Transaction End Date:</strong> {formatDate(settlement.transact_max_dt)}</p>
          <p><strong>Transaction Count:</strong> {settlement.transact_count}</p>
          <p><strong>Paid Date:</strong> {formatDate(settlement.settle_pay_dt)}</p>
          <p><strong>Expected Payment:</strong> {formatCurrency(settlement.settle_exp_amt)}</p>
          <p><strong>Amount Paid:</strong> {formatCurrency(settlement.settle_pay_amt)}</p>
          <p><strong>Amount Disputed:</strong> {formatCurrency(settlement.dispute_amt)}</p>
          <p><strong>Dispute Reason:</strong> {settlement.dispute_reason}</p>
          <p><strong>Days Late:</strong> {settlement.days_late}</p>
          <p><strong>Late Fee Amount:</strong> {formatCurrency(settlement.late_fee_amt)}</p>
          <p><strong>Residual Payment Date:</strong> {formatDate(settlement.residual_pay_dt)}</p>
          <p><strong>Residual Expected Amount:</strong> {formatCurrency(settlement.residual_exp_amt)}</p>
          <p><strong>Residual Calculated Amount:</strong> {formatCurrency(settlement.residual_calc_amt)}</p>
          <p><strong>Residual Paid Amount:</strong> {formatCurrency(settlement.residual_pay_amt)}</p>
        </>
      ) : (
        <>
          <p><strong>Contract:</strong></p>
          <p><strong>Due Date:</strong></p>
          <p><strong>Transaction Start Date:</strong></p>
          <p><strong>Transaction End Date:</strong></p>
          <p><strong>Transaction Count:</strong></p>
          <p><strong>Paid Date:</strong></p>
          <p><strong>Expected Payment:</strong></p>
          <p><strong>Amount Paid:</strong></p>
          <p><strong>Amount Disputed:</strong></p>
          <p><strong>Dispute Reason:</strong></p>
          <p><strong>Days Late:</strong></p>
          <p><strong>Late Fee Amount:</strong></p>
          <p><strong>Residual Payment Date:</strong></p>
          <p><strong>Residual Expected Amount:</strong></p>
          <p><strong>Residual Paid Amount:</strong></p>
        </>
      )}
    </div>
  );
};

export default SettlementDetail;
