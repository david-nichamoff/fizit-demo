import React, { useState, useEffect } from 'react';
import ValueChart from './ValueChart'; 
import Pagination from './Pagination';
import TransactionDetail from './TransactionDetail'
import { formatCurrency, formatDateTime } from './Utils';
import FilterContainer from './FilterContainer'; 
import axios from 'axios';
import './TransactionsPage.css';

const TransactionsPage = ({ transactions }) => {
  const itemsPerPage = 12;
  const [contracts, setContracts] = useState([]);
  const [selectedContracts, setSelectedContracts] = useState([]);
  const [dateFrom, setDateFrom] = useState(null);
  const [dateTo, setDateTo] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
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

  // Filter transactions based on selected contracts and date range
  const filteredTransactions = transactions.filter((transaction) => {
    if (selectedContracts.length > 0 && !selectedContracts.includes(transaction.contract_name)) {
      return false;
    }
    if (dateFrom && new Date(transaction.transact_dt) < new Date(dateFrom)) {
      return false;
    }
    if (dateTo && new Date(transaction.transact_dt) > new Date(dateTo)) {
      return false;
    }
    return true;
  });

  const totalPages = Math.ceil(filteredTransactions.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, filteredTransactions.length);
  const visibleTransactions = filteredTransactions.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleTransactionSelect = (transaction) => {
    setSelectedTransaction(transaction);
  };

  return (
    <div className="detail-page">
      <FilterContainer 
        onApplyFilters={applyFilters} 
        contracts={contracts} 
        header="Transactions"
      />
      <div className="transaction-container">
        <div className="transaction-header">
          <div className="column-header string-column">Contract</div>
          <div className="column-header time-column">Date</div>
          <div className="column-header amount-column">Amount</div>
          <div className="column-header amount-column">Advanced</div>
        </div>
        <ul className="transaction-list">
          {visibleTransactions.map((transaction, index) => (
            <li 
              key={index} 
              className={`transaction-item ${transaction === selectedTransaction ? 'selected' : ''}`}
              onClick={() => handleTransactionSelect(transaction)}
            >
              <div className="transaction-column string-column">{transaction.contract_name}</div>
              <div className="transaction-column time-column">{formatDateTime(transaction.transact_dt)}</div>
              <div className="transaction-column amount-column">{formatCurrency(transaction.transact_amt)}</div>
              <div className="transaction-column amount-column">{formatCurrency(transaction.advance_pay_amt)}</div>
            </li>
          ))}
        </ul>
        <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
      </div>
      <TransactionDetail transaction={selectedTransaction} /> 
      {!isInitialLoad && <ValueChart transactions={filteredTransactions} />} 
    </div>
  );
};

export default TransactionsPage;
