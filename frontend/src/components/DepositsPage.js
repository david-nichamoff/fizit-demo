import React, { useState, useEffect } from 'react';
import Pagination from './Pagination';
import { formatCurrency, formatDateTime, formatDate } from './Utils';
import FilterContainer from './FilterContainer';
import axios from 'axios';
import './DepositsPage.css';

const DepositsPage = ({ deposits, contracts }) => {
  const itemsPerPage = 12;
  const [settlementPeriods, setSettlementPeriods] = useState([]);
  const [selectedContracts, setSelectedContracts] = useState([]);
  const [dateFrom, setDateFrom] = useState(null);
  const [dateTo, setDateTo] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedDeposit, setSelectedDeposit] = useState(null);
  const [selectedContract, setSelectedContract] = useState(null);
  const [selectedSettlementPeriod, setSelectedSettlementPeriod] = useState(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  useEffect(() => {
    setIsInitialLoad(false);
  }, []);

  const applyFilters = (selectedContracts, fromDate, toDate) => {
    setSelectedContracts(selectedContracts);
    setDateFrom(fromDate);
    setDateTo(toDate);
    setCurrentPage(1); // Reset pagination to first page
  };

  const fetchSettlementPeriods = async (contractId) => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL}/settlements?contract_id=${contractId}`);
      setSettlementPeriods(response.data);
    } catch (error) {
      console.error('Error fetching settlement periods:', error);
    }
  };

  // Filter deposits based on selected contracts and date range
  const filteredDeposits = deposits.filter((deposit) => {
    if (selectedContracts.length > 0 && !selectedContracts.includes(deposit.contract_name)) {
      return false;
    }
    if (dateFrom && new Date(deposit.deposit_dt) < new Date(dateFrom)) {
      return false;
    }
    if (dateTo && new Date(deposit.deposit_dt) > new Date(dateTo)) {
      return false;
    }
    return true;
  });

  const totalPages = Math.ceil(filteredDeposits.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, filteredDeposits.length);
  const visibleDeposits = filteredDeposits.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleDepositSelect = (deposit) => {
    setSelectedDeposit(deposit);
    const contract = contracts.find(c => c.contract_name === deposit.contract_name);
    if (contract) {
      fetchSettlementPeriods(contract.contract_id); // Fetch settlement periods for the selected contract
      setSelectedContract(contract);
    }
  };

  const handleLinkDeposit = () => {
    // Logic to link deposit to the selected settlement period
    // API call to link deposit with settlement period
  };

  return (
    <div className="detail-page">
      <FilterContainer 
        onApplyFilters={applyFilters} 
        items={contracts} 
        header="Deposits"
        displayKey="contract_name"
      />
      <div className="deposit-container">
        <div className="deposit-header">
          <div className="column-header string-column">Contract</div>
          <div className="column-header amount-column">Amount</div>
          <div className="column-header date-column">Deposit Date</div>
          <div className="column-header string-column">Counterparty</div>
        </div>
        <ul className="deposit-list">
          {visibleDeposits.map((deposit, index) => (
            <li 
              key={index} 
              className={`deposit-item ${deposit === selectedDeposit ? 'selected' : ''}`}
              onClick={() => handleDepositSelect(deposit)}
            >
              <div className="deposit-column string-column">{deposit.contract_name}</div>
              <div className="deposit-column amount-column">{formatCurrency(deposit.amount)}</div>
              <div className="deposit-column date-column">{formatDateTime(deposit.deposit_dt)}</div>
              <div className="deposit-column string-column">{deposit.counterparty}</div>
            </li>
          ))}
        </ul>
        <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
      </div>
      {selectedDeposit && selectedContract && (
        <div className="settlement-periods-container">
          <h3>Select Settlement Period</h3>
          <ul className="settlement-periods-list">
            {settlementPeriods.map((period, index) => (
              <li 
                key={index} 
                className={`settlement-period-item ${period === selectedSettlementPeriod ? 'selected' : ''}`}
                onClick={() => setSelectedSettlementPeriod(period)}
              >
                {formatDate(period.start_date)} - {formatDate(period.end_date)}
              </li>
            ))}
          </ul>
          <button 
            onClick={handleLinkDeposit} 
            disabled={!selectedSettlementPeriod}
          >
            Link Deposit to Settlement Period
          </button>
        </div>
      )}
    </div>
  );
};

export default DepositsPage;