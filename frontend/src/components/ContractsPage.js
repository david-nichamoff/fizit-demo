import React, { useState, useEffect } from 'react';
import axios from 'axios';
import uc from '../assets/image/under_construction_pc_800_wht.jpg'; 
import { formatPercentage, formatCurrency } from './Utils';
import './ContractsPage.css';

const formatJsonAsGrid = (jsonObject) => {
  return (
    <>
      {Object.entries(jsonObject).map(([key, value], index) => (
        <React.Fragment key={index}>
          <div className="json-key">{key}</div>
          <div className="json-value">{value}</div>
        </React.Fragment>
      ))}
    </>
  );
};

const ContractsPage = () => {
  const [contracts, setContracts] = useState([]);

  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const response = await axios.get(`${process.env.REACT_APP_API_URL}/contracts`);
        setContracts(response.data);
      } catch (error) {
        console.error('Error fetching contracts:', error);
      }
    };

    fetchContracts();
  }, []);

  return (
    <div className="contracts-page">
      {contracts.map((contract, index) => (
        <div key={index} className="contract-container">
          <h2 className="contract-header">
            {contract.contract_name} {!contract.is_active && <span className="inactive-text">(- Inactive)</span>}
          </h2>
          <div className="contract-grid">
            <div className="header-row">Identifiers</div>
            {formatJsonAsGrid(contract.extended_data)}
            <div className="header-row">Funding Instructions</div>
            {formatJsonAsGrid(contract.funding_instr)}
            <div className="header-row">Financial Details</div>
            <div className="json-key">Service Fee Pct</div>
            <div className="json-value">{formatPercentage(contract.service_fee_pct)}</div>
            <div className="json-key">Service Fee Amt</div>
            <div className="json-value">{formatCurrency(contract.service_fee_amt)}</div>
            <div className="json-key">Advance Pct</div>
            <div className="json-value">{formatPercentage(contract.advance_pct)}</div>
            <div className="json-key">Late Fee Pct</div>
            <div className="json-value">{formatPercentage(contract.late_fee_pct)}</div>
            <div className="header-row">Transaction Logic</div>
            <div className="json-value transaction-logic">{JSON.stringify(contract.transact_logic)}</div>
          </div>
        </div>
      ))}
      <div className="request-quote-container">
        <h2>Request a Quote</h2>
        <img src={uc} alt="Under Construction" className="uc" />
      </div>
      <div className="ambassador-container">
        <h2>Become an Ambassador</h2>
        <img src={uc} alt="Under Construction" className="uc" />
      </div>
    </div>
  );
};

export default ContractsPage;