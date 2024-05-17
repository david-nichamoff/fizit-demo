import React from 'react';
import './ContractsPage.css';

const ContractsPage = ({ contracts }) => {
  console.log('Contracts:', contracts);

  return (
    <div className="detail-page">
      <h1>Contract Overview</h1>
      <ul className="contracts-list">
        {contracts.map((contract, index) => (
          <li key={index} className="contract-item">
            <div className="contract-container">
              <strong>{contract.contract_name}</strong>
              <p>Contract ID: {contract.ext_id.contract}</p>
              <p>Payment ID: {contract.payment_instr.id}</p>
              <p>Bank: {contract.funding_instr.bank}</p>
              <p>Account: {contract.funding_instr.account}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ContractsPage;
