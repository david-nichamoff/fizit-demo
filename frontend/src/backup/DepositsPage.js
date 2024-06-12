import React, { useState, useEffect } from 'react';
import Pagination from './Pagination';
import { formatCurrency, formatDateTime, formatDate } from './Utils';
import axios from 'axios';
import './DepositsPage.css';

const DepositsPage = () => {
  const itemsPerPage = 12;
  const [accounts, setAccounts] = useState([]);
  const [deposits, setDeposits] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedDeposit, setSelectedDeposit] = useState(null);
  const [settlementPeriods, setSettlementPeriods] = useState([]);
  const [selectedSettlementPeriod, setSelectedSettlementPeriod] = useState(null);

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

  const fetchDeposits = async (accountId) => {
    try {
      const today = new Date();
      const oneYearAgo = new Date(today);
      oneYearAgo.setFullYear(today.getFullYear() - 1);

      const endDate = today.toISOString().slice(0, 10);
      const startDate = oneYearAgo.toISOString().slice(0, 10);

      const response = await axios.get(`${process.env.REACT_APP_API_URL}/accounts/${accountId}/deposits/`, {
        params: {
          start_date: startDate,
          end_date: endDate
        }
      });
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

  const handleAccountSelect = (account) => {
    setSelectedAccount(account);
    setSelectedDeposit(null);
    setDeposits([]);
    fetchDeposits(account.account_id);
    fetchSettlementPeriods(account.account_id);
  };

  const handleDepositSelect = (deposit) => {
    setSelectedDeposit(deposit);
  };

  const handleLinkDeposit = async () => {
    if (selectedSettlementPeriod) {
      try {
        await axios.post(`${process.env.REACT_APP_API_URL}/api/accounts/${selectedSettlementPeriod.contract_idx}/post_settlement`);
        alert('Deposit successfully linked to settlement period.');
      } catch (error) {
        console.error('Error linking deposit to settlement period:', error);
        alert('Failed to link deposit to settlement period.');
      }
    }
  };

  return (
    <div className="detail-page">
      <div className="account-container">
        <h2>Accounts</h2>
        <div className="account-header">
          <div className="column-header shortstring-column">Bank</div>
          <div className="column-header string-column">Account Name</div>
          <div className="column-header amount-column">Balance</div>
        </div>
        <ul className="account-list">
          {accounts.map((account, index) => (
            <li
              key={index}
              className={`account-item ${account === selectedAccount ? 'selected' : ''}`}
              onClick={() => handleAccountSelect(account)}
            >
              <div className="account-column shortstring-column">{account.bank}</div>
              <div className="account-column string-column">{account.account_name}</div>
              <div className="account-column amount-column">{formatCurrency(account.available_balance)}</div>
            </li>
          ))}
        </ul>
      </div>

      {selectedAccount && (
        <div className="deposit-container">
          <h2>Deposits</h2>
          <div className="deposit-header">
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
                <div className="deposit-column amount-column">{formatCurrency(deposit.deposit_amt)}</div>
                <div className="deposit-column date-column">{formatDateTime(deposit.deposit_dt)}</div>
                <div className="deposit-column string-column">{deposit.counterparty}</div>
              </li>
            ))}
          </ul>
          <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
        </div>
      )}

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