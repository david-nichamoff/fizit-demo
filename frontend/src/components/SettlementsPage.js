import React, { useState, useEffect } from 'react';
import Pagination from './Pagination';
import SettlementDetail from './SettlementDetail';
import { formatCurrency, formatDate } from './Utils';
import FilterContainer from './FilterContainer'; 
import axios from 'axios';
import './SettlementsPage.css';

const SettlementsPage = ({ settlements }) => {
  const itemsPerPage = 12;
  const [contracts, setContracts] = useState([]);
  const [selectedContracts, setSelectedContracts] = useState([]);
  const [dateFrom, setDateFrom] = useState(null);
  const [dateTo, setDateTo] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedSettlement, setSelectedSettlement] = useState(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

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

  useEffect(() => {
    setIsInitialLoad(false);
  }, []);

  const applyFilters = (selectedContracts, fromDate, toDate) => {
    setSelectedContracts(selectedContracts);
    setDateFrom(fromDate);
    setDateTo(toDate);
    setCurrentPage(1); // Reset pagination to first page
  };

  // Filter settlements based on selected contracts and date range
  const filteredSettlements = settlements.filter((settlement) => {
    if (selectedContracts.length > 0 && !selectedContracts.includes(settlement.contract_name)) {
      return false;
    }
    if (dateFrom && new Date(settlement.settle_due_dt) < new Date(dateFrom)) {
      return false;
    }
    if (dateTo && new Date(settlement.settle_due_dt) > new Date(dateTo)) {
      return false;
    }
    return true;
  });

  const averageDaysLate = (filteredSettlements.reduce((sum, settlement) => sum + settlement.days_late, 0) / filteredSettlements.length).toFixed(1);
  const averageLateFee = (filteredSettlements.reduce((sum, settlement) => sum + settlement.late_fee_amt, 0) / filteredSettlements.length).toFixed(2);
  const averageDisputeAmt = (filteredSettlements.reduce((sum, settlement) => sum + settlement.dispute_amt, 0) / filteredSettlements.length).toFixed(2);

  const totalPages = Math.ceil(filteredSettlements.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, filteredSettlements.length);
  const visibleSettlements = filteredSettlements.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleSettlementSelect = (settlement) => {
    setSelectedSettlement(settlement);
  };

  const isOverdueUnpaid = (settlement) => {
    const today = new Date();
    const dueDate = new Date(settlement.settle_due_dt);
    return today > dueDate && settlement.settle_pay_amt === 0;
  };

  return (
    <div className="detail-page">
      <FilterContainer 
        onApplyFilters={applyFilters} 
        items={contracts} 
        dropdown_text = "Contracts"
        header="Settlements"
        displayKey="contract_name"
      />
      <div className="settlement-container">
        <div className="settlement-header">
          <div className="column-header string-column">Contract</div>
          <div className="column-header date-column">Due Date</div>
          <div className="column-header number-column">Transactions</div>
          <div className="column-header amount-column">Expected</div>
          <div className="column-header amount-column">Paid</div>
        </div>
        <ul className="settlement-list">
          {visibleSettlements.map((settlement, index) => (
            <li 
              key={index} 
              className={`settlement-item ${settlement === selectedSettlement ? 'selected' : ''} ${isOverdueUnpaid(settlement) ? 'overdue-unpaid' : ''}`}
              onClick={() => handleSettlementSelect(settlement)}
            >
              <div className="settlement-column string-column">{settlement.contract_name}</div>
              <div className="settlement-column date-column">{formatDate(settlement.settle_due_dt)}</div>
              <div className="settlement-column number-column">{settlement.transact_count}</div>
              <div className="settlement-column amount-column">{formatCurrency(settlement.settle_exp_amt)}</div>
              <div className="settlement-column amount-column">{formatCurrency(settlement.settle_pay_amt)}</div>
            </li>
          ))}
        </ul>
        <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
      </div>
      {selectedSettlement && (
        <div className="settlement-detail-wrapper">
          <SettlementDetail settlement={selectedSettlement} />
        </div>
      )}
      <div className="stats-container">
        <div className="late-fee-container">
          <p>
            Average Late Fee<br /><span className="amount">{formatCurrency(averageLateFee)}</span>
          </p>
        </div>
        <div className="dispute-container">
          <p>
            Average Dispute Amount<br /><span className="amount">{formatCurrency(averageDisputeAmt)}</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default SettlementsPage;