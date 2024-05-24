import React, { useState, useEffect } from 'react';
import Pagination from './Pagination';
import { formatCurrency, formatDateTime, formatDate } from './Utils';
import FilterContainer from './FilterContainer';
import axios from 'axios';
import './DepositsPage.css';

const DepositsPage = () => {
  const itemsPerPage = 12;
  const [deposits, setDeposits] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [settlementPeriods, setSettlementPeriods] = useState([]);
  const [selectedAccounts, setSelectedAccounts] = useState([]);
  const [dateFrom, setDateFrom] = useState(null);
  const [dateTo, setDateTo] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedDeposit, setSelectedDeposit] = useState(null);
  const [selectedSettlementPeriod, setSelectedSettlementPeriod] = useState(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const response = await axios.get(`${process.env.REACT_APP_API_URL}/accounts`);
        setAccounts(response.data);
      } catch (error) {
        console.error('Error fetching accounts:', error);
      }
    };

    fetchAccounts();
  }, []);

  useEffect(() => {
    fetchDeposits([], null, null);
    setIsInitialLoad(false);
  }, []);

  const applyFilters = (selectedAccounts, fromDate, toDate) => {
    setSelectedAccounts(selectedAccounts);
    setDateFrom(fromDate);
    setDateTo(toDate);
    setCurrentPage(1); 
    fetchDeposits(selectedAccounts, fromDate, toDate); 
  };

  const fetchDeposits = async (selectedAccounts, fromDate, toDate) => {
    try {
      const params = {};
      if (selectedAccounts.length > 0) {
        params.account_ids = selectedAccounts.join(',');
      }
      if (fromDate) {
        params.start_date = fromDate;
      }
      if (toDate) {
        params.end_date = toDate;
      }

      const response = await axios.get(`${process.env.REACT_APP_API_URL}/deposits`, { params });
      setDeposits(response.data);
    } catch (error) {
      console.error('Error fetching deposits:', error);
    }
  };

  const fetchSettlementPeriods = async (accountId) => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL}/settlements`, { params: { account_id: accountId } });
      const validSettlementPeriods = response.data.filter(period => period.settle_exp_amt > 0);
      setSettlementPeriods(validSettlementPeriods);
    } catch (error) {
      console.error('Error fetching settlement periods:', error);
    }
  };

  const totalPages = Math.ceil(deposits.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, deposits.length);
  const visibleDeposits = deposits.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleDepositSelect = (deposit) => {
    setSelectedDeposit(deposit);
    fetchSettlementPeriods(deposit.account_id);
  };

  const handleLinkDeposit = async () => {
    if (selectedSettlementPeriod) {
      try {
        await axios.post(`${process.env.REACT_APP_API_URL}/contracts/${selectedSettlementPeriod.contract_idx}/post_settlement`);
        alert('Deposit successfully linked to settlement period.');
      } catch (error) {
        console.error('Error linking deposit to settlement period:', error);
        alert('Failed to link deposit to settlement period.');
      }
    }
  };

  return (
    <div className="detail-page">
      <FilterContainer 
        onApplyFilters={applyFilters} 
        items={accounts} 
        dropdown_text="Accounts"
        header="Deposits"
        displayKey="account_name"
      />
      <div className="deposit-container">
        <div className="deposit-header">
          <div className="column-header string-column">Account</div>
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
              <div className="deposit-column string-column">{deposit.account_name}</div>
              <div className="deposit-column amount-column">{formatCurrency(deposit.deposit_amt)}</div>
              <div className="deposit-column date-column">{formatDateTime(deposit.deposit_dt)}</div>
              <div className="deposit-column string-column">{deposit.counterparty}</div>
            </li>
          ))}
        </ul>
        <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
      </div>
      {selectedDeposit && (
        <div className="settlement-periods-container">
          <h2>Settlement Period</h2>
          <div className="settlement-periods-header">
            <div className="column-header string-column">Contract</div>
            <div className="column-header date-column">Due Date</div>
            <div className="column-header amount-column">Expected Amount</div>
          </div>
          <ul className="settlement-periods-list">
            {settlementPeriods.map((period, index) => (
              <li 
                key={index} 
                className={`settlement-period-item ${period === selectedSettlementPeriod ? 'selected' : ''}`}
                onClick={() => setSelectedSettlementPeriod(period)}
              >
                <div className="settlement-period-column string-column">{period.contract_name}</div>
                <div className="settlement-period-column date-column">{formatDate(period.settle_due_dt)}</div>
                <div className="settlement-period-column amount-column">{formatCurrency(period.settle_exp_amt)}</div>
              </li>
            ))}
          </ul>
          <button 
            className="link-button"
            onClick={handleLinkDeposit} 
            disabled={!selectedDeposit || !selectedSettlementPeriod}
          >
            Link Deposit to Settlement Period
          </button>
        </div>
      )}
    </div>
  );
};

export default DepositsPage;