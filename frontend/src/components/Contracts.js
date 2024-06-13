import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import engageImage from '../../static/assets/image/engage.jpg';
import { formatCurrency, formatPercentage, capitalizeFirstLetter } from './Utils';
import Settlements from './Settlements'; // Import the Settlements component
import './Contracts.css';
import Cookies from 'js-cookie';

const Contracts = ({ contracts, user }) => {
  const [parties, setParties] = useState({});
  const [selectedContractIdx, setSelectedContractIdx] = useState(null); // Track selected contract
  const containerRef = useRef(null);

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
        console.log(`Fetched parties for contract ${contractIdx}:`, response.data);
        setParties(prevParties => ({ ...prevParties, [contractIdx]: response.data }));
      } catch (error) {
        console.error(`Error fetching parties for contract ${contractIdx}:`, error);
      }
    };

    contracts.forEach(contract => {
      fetchParties(contract.contract_idx);
    });
  }, [contracts, user]);

  const renderParties = (contractIdx) => {
    return (parties[contractIdx] || []).map((party, index) => (
      <div key={index} className="party-data">{`${party.party_type}: ${party.party_code}`}</div>
    ));
  };

  const renderContractDetails = (contract) => {
    if (contract.contract_type === 'ticketing') {
      return (
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
      );
    }
    return null;
  };

  const handleContractClick = (contractIdx) => {
    setSelectedContractIdx(contractIdx); 
  };

  const scrollLeft = () => {
    containerRef.current.scrollBy({ left: -300, behavior: 'smooth' });
  };

  const scrollRight = () => {
    containerRef.current.scrollBy({ left: 300, behavior: 'smooth' });
  };

  return (
    <div className="contracts-scroll-container">
      <button className="scroll-arrow scroll-arrow-left" onClick={() => containerRef.current.scrollBy({ left: -300, behavior: 'smooth' })}>&lt;</button>
      <div className="contracts-container" ref={containerRef}>
        {contracts.map((contract, index) => (
          <div
            key={index}
            className={`contract-container ${selectedContractIdx === contract.contract_idx ? 'selected' : ''}`}
            onClick={() => handleContractClick(contract.contract_idx)}
          >
            <h2 className="contract-header">
              {contract.contract_name.length > 30 ? `${contract.contract_name.substring(0, 30)}...` : contract.contract_name}
              {!contract.is_active && <span className="inactive-text">(- Inactive)</span>}
            </h2>
            {contract.contract_type === 'ticketing' && contract.extended_data.provider === 'engage' && (
              <img src={engageImage} alt="Engage" className="engage-image" />
            )}
            {renderContractDetails(contract)}
          </div>
        ))}
      </div>
      <button className="scroll-arrow scroll-arrow-right" onClick={scrollRight}>&gt;</button>
      {selectedContractIdx && <Settlements contractIdx={selectedContractIdx} />} 
    </div>
  );
};

export default Contracts;