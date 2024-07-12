import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { formatCurrency, formatPercentage, formatDate } from './Utils';
import './Contracts.css';
import Cookies from 'js-cookie';

const Contracts = ({ contracts, user }) => {
  const [parties, setParties] = useState({});
  const [expandedContracts, setExpandedContracts] = useState([]);
  const [settlements, setSettlements] = useState({});
  const [transactions, setTransactions] = useState({});
  const [selectedContractIdx, setSelectedContractIdx] = useState(null); 
  const [expandedTransactions, setExpandedTransactions] = useState([]);
  const [contractListWidth, setContractListWidth] = useState(400); 
  const containerRef = useRef(null);
  const isResizing = useRef(false);

  useEffect(() => {
    const fetchParties = async (contractIdx) => {
      try {
        const csrfToken = Cookies.get('csrftoken');
        const response = await axios.get(`${process.env.REACT_APP_API_URL}/contracts/${contractIdx}/parties`, {
          withCredentials: true,
          headers: {
            'X-CSRFToken': csrfToken
          }
        });
        setParties(prevParties => ({ ...prevParties, [contractIdx]: response.data }));
      } catch (error) {
        console.error(`Error fetching parties for contract ${contractIdx}:`, error);
      }
    };

    contracts.forEach(contract => {
      fetchParties(contract.contract_idx);
    });
  }, [contracts, user]);

  const fetchSettlements = async (contractIdx) => {
    try {
      const response = await axios.get(`/api/contracts/${contractIdx}/settlements`, {
        withCredentials: true,
      });
      setSettlements(prevSettlements => ({ ...prevSettlements, [contractIdx]: response.data }));
    } catch (error) {
      console.error(`Error fetching settlements for contract ${contractIdx}:`, error);
    }
  };

  const fetchTransactions = async (contractIdx) => {
    try {
      const response = await axios.get(`/api/contracts/${contractIdx}/transactions`, {
        withCredentials: true,
      });
      setTransactions(prevTransactions => ({ ...prevTransactions, [contractIdx]: response.data }));
    } catch (error) {
      console.error(`Error fetching transactions for contract ${contractIdx}:`, error);
    }
  };

  const renderParties = (contractIdx) => {
    return (parties[contractIdx] || []).map((party, index) => (
      <div key={index} className="party-data">{`${party.party_type}: ${party.party_code}`}</div>
    ));
  };

  const renderSettlements = (contractIdx) => {
    const today = new Date();
    return (settlements[contractIdx] || []).map((settlement, index) => {
      if (settlement.settle_exp_amt === 0) return null;
      const isLate = new Date(settlement.settle_due_dt) < today;
      return (
        <div
          key={index}
          className={`settlement-item ${selectedContractIdx === contractIdx ? 'selected' : ''}`}
        >
          <span>{`Due Date: ${formatDate(settlement.settle_due_dt)}, Amount Due: ${formatCurrency(settlement.settle_exp_amt)}`}</span>
          {isLate && <span className="late-label">Late</span>}
        </div>
      );
    });
  };

  const renderContractDetails = (contract) => {
    if (contract.contract_type === 'ticketing') {
      return (
        <>
          <div className="contract-details">
            <div className="detail-column">
              {renderParties(contract.contract_idx)}
            </div>
            <div className="detail-column">
              <div className="detail-item">Advance Fee: {formatPercentage(contract.service_fee_pct)} + {formatCurrency(contract.service_fee_amt)}</div>
              <div className="detail-item">Amount Advanced: {formatPercentage(contract.advance_pct)}</div>
              <div className="detail-item">Late Fee (APR): {formatPercentage(contract.late_fee_pct)}</div>
            </div>
          </div>
          <div className="settlements-container">
            {renderSettlements(contract.contract_idx)}
          </div>
        </>
      );
    }
    return null;
  };

  const renderTransactions = (contractIdx) => {
    return (transactions[contractIdx] || []).map((transaction, index) => (
      <div key={index} className="transaction-item">
        <div className="transaction-header-container">
          <span>{`Transaction Date: ${formatDate(transaction.transact_dt)}, Amount: ${formatCurrency(transaction.transact_amt)}, Amount Advanced: ${formatCurrency(transaction.advance_amt)}`}</span>
          <button className="expand-button" onClick={(e) => { e.stopPropagation(); handleTransactionExpandClick(contractIdx, index); }}>
            {expandedTransactions.includes(index) ? '▼' : '▶'}
          </button>
        </div>
        {expandedTransactions.includes(index) && (
          <div className="transaction-details">
            <div className="detail-column">
              <div className="detail-item">{`Transaction Date: ${formatDate(transaction.transact_dt)}`}</div>
              <div className="detail-item">{`Transaction Amount: ${formatCurrency(transaction.transact_amt)}`}</div>
              <div className="detail-item">{`Advance Pay Date: ${formatDate(transaction.advance_pay_dt)}`}</div>
              <div className="detail-item">{`Advance Pay Amount: ${formatCurrency(transaction.advance_pay_amt)}`}</div>
            </div>
            <div className="detail-column">
              {Object.entries(transaction.extended_data).map(([key, value], i) => (
                <div key={i} className="detail-item">{`${key}: ${value}`}</div>
              ))}
            </div>
          </div>
        )}
      </div>
    ));
  };

  const handleContractClick = (contractIdx) => {
    setSelectedContractIdx(contractIdx);
    fetchTransactions(contractIdx);
  };

  const handleExpandClick = (contractIdx) => {
    if (expandedContracts.includes(contractIdx)) {
      setExpandedContracts(expandedContracts.filter(idx => idx !== contractIdx));
    } else {
      setExpandedContracts([...expandedContracts, contractIdx]);
      fetchSettlements(contractIdx);
    }
  };

  const handleTransactionExpandClick = (contractIdx, index) => {
    if (expandedTransactions.includes(index)) {
      setExpandedTransactions(expandedTransactions.filter(i => i !== index));
    } else {
      setExpandedTransactions([...expandedTransactions, index]);
    }
  };

  const handleMouseDown = (e) => {
    isResizing.current = true;
  };

  const handleMouseMove = (e) => {
    if (isResizing.current) {
      const newWidth = e.clientX;
      if (newWidth > 100 && newWidth < window.innerWidth - 100) {
        setContractListWidth(newWidth);
      }
    }
  };

  const handleMouseUp = () => {
    isResizing.current = false;
  };

  useEffect(() => {
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  return (
    <div className="contracts-main-container" style={{ gridTemplateColumns: `${contractListWidth}px 1fr` }}>
      <div className="contracts-list">
        <h2 className="contracts-header">Contracts</h2>
        {contracts.map((contract, index) => (
          <div
            key={index}
            className={`contract-item ${selectedContractIdx === contract.contract_idx ? 'selected' : ''}`}
            onClick={() => handleContractClick(contract.contract_idx)}
          >
            <div className="contract-header-container">
              <h2 className="contract-header" title={contract.contract_name}>
                {contract.contract_name.length > 30 ? `${contract.contract_name.substring(0, 30)}...` : contract.contract_name}
              </h2>
              <button className="expand-button" onClick={(e) => { e.stopPropagation(); handleExpandClick(contract.contract_idx); }}>
                {expandedContracts.includes(contract.contract_idx) ? '▼' : '▶'}
              </button>
            </div>
            {expandedContracts.includes(contract.contract_idx) && (
              <div className="contract-details-container">
                {renderContractDetails(contract)}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="transactions-list">
        <h2 className="transactions-header">Transactions</h2>
        {selectedContractIdx && renderTransactions(selectedContractIdx)}
      </div> 
    </div>
  );
};

export default Contracts;