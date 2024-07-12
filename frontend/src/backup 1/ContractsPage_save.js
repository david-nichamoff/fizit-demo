import React from 'react';
import engageImage from '../../static/assets/image/engage.jpg'; // Import the image
import { formatCurrency, formatPercentage, capitalizeFirstLetter } from './Utils';
import './ContractsPage.css';

const ContractsPage = ({ contracts }) => {
  const renderContractDetails = (contract) => {
    const provider = contract.extended_data.provider ? capitalizeFirstLetter(contract.extended_data.provider) : '';

    if (contract.contract_type === 'ticketing') {
      return (
        <div className="contract-details">
          <div className="detail-column">
            <div className="detail-item">Ticket Provider: {provider}</div>
            <div className="detail-item">Source: {contract.extended_data.src_code}</div>
            <div className="detail-item">Destination: {contract.extended_data.dest_code}</div>
          </div>
          <div className="detail-column">
            <div className="detail-item">Advance Fee: {formatPercentage(contract.service_fee_pct)} + {formatCurrency(contract.service_fee_amt)}</div>
            <div className="detail-item">Amount Advanced: {formatPercentage(contract.advance_pct)}</div>
            <div className="detail-item">Late Fee (APR): {formatPercentage(contract.late_fee_pct)}</div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="contracts-container">
      {contracts.map((contract, index) => (
        <div key={index} className="contract-container">
          <h2 className="contract-header">
            {contract.contract_name} {!contract.is_active && <span className="inactive-text">(- Inactive)</span>}
          </h2>
          {contract.contract_type === 'ticketing' && contract.extended_data.provider === 'engage' && (
            <img src={engageImage} alt="Engage" className="engage-image" />
          )}
          {renderContractDetails(contract)}
        </div>
      ))}
    </div>
  );
};

export default ContractsPage;