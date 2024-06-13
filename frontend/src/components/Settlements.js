import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { formatCurrency, formatDate } from './Utils';
import './Settlements.css';

const Settlements = ({ contractIdx }) => {
  const [settlements, setSettlements] = useState([]);

  useEffect(() => {
    axios.get(`/api/contracts/${contractIdx}/settlements`)
      .then(response => setSettlements(response.data))
      .catch(error => console.error(`Error fetching settlements for contract ${contractIdx}:`, error));
  }, [contractIdx]);

  return (
    <div className="settlement-container">
      <h2>Settlements</h2>
      {settlements.map((settlement, index) => (
        <div key={index} className="settlement-detail-container">
          <div className="settlement-grid">
            <div className="header-row">Settlement Period Details</div>
            <div className="json-key">Contract Name</div>
            <div className="json-value">{settlement.contract_name}</div>
            <div className="json-key">Due Date</div>
            <div className="json-value">{formatDate(settlement.settle_due_dt)}</div>
            <div className="json-key">Transaction Start Date</div>
            <div className="json-value">{formatDate(settlement.transact_min_dt)}</div>
            <div className="json-key">Transaction End Date</div>
            <div className="json-value">{formatDate(settlement.transact_max_dt)}</div>
            <div className="json-key">Transaction Count</div>
            <div className="json-value">{settlement.transact_count}</div>
            
            <div className="header-row">Payment Details</div>
            <div className="json-key">Paid Date</div>
            <div className="json-value">{formatDate(settlement.settle_pay_dt)}</div>
            <div className="json-key">Expected Payment</div>
            <div className="json-value">{formatCurrency(settlement.settle_exp_amt)}</div>
            <div className="json-key">Amount Paid</div>
            <div className="json-value">{formatCurrency(settlement.settle_pay_amt)}</div>
            <div className="json-key">Amount Disputed</div>
            <div className="json-value">{formatCurrency(settlement.dispute_amt)}</div>
            <div className="json-key">Dispute Reason</div>
            <div className="json-value">{settlement.dispute_reason}</div>
            <div className="json-key">Days Late</div>
            <div className="json-value">{settlement.days_late}</div>
            <div className="json-key">Late Fee Amount</div>
            <div className="json-value">{formatCurrency(settlement.late_fee_amt)}</div>

            <div className="header-row">Residual Payment Details</div>
            <div className="json-key">Residual Payment Date</div>
            <div className="json-value">{formatDate(settlement.residual_pay_dt)}</div>
            <div className="json-key">Residual Expected Amount</div>
            <div className="json-value">{formatCurrency(settlement.residual_exp_amt)}</div>
            <div className="json-key">Residual Calculated Amount</div>
            <div className="json-value">{formatCurrency(settlement.residual_calc_amt)}</div>
            <div className="json-key">Residual Paid Amount</div>
            <div className="json-value">{formatCurrency(settlement.residual_pay_amt)}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Settlements;