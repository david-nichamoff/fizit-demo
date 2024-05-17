import React, { useState, useEffect } from 'react';
import NavBar from './components/NavBar';
import ContractsPage from './components/ContractsPage';
import SettlementsPage from './components/SettlementsPage';
import TransactionsPage from './components/TransactionsPage';
import ArtifactsPage from './components/ArtifactsPage';
import DemoPage from './components/DemoPage';
import axios from 'axios';
import './App.css';

const App = () => {
  const [contracts, setContracts] = useState([]);
  const [settlements, setSettlements] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [artifacts, setArtifacts] = useState([]);

  const [displayPage, setDisplayPage] = useState('contracts'); // Default page to display

  const fetchData = async (url, setData) => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL}${url}`);
      const responseData = response.data;

      if (Array.isArray(responseData)) {

        setData(responseData);
      } else {
        console.error(`API response is not an array for ${url}:`, responseData);
      }
    } catch (error) {
      console.error(`Error fetching data for ${url}:`, error);
    }
  };

  useEffect(() => {
    fetchData('/contracts', setContracts);
  }, []);

  const handleViewChange = (page) => {
    setDisplayPage(page);
    switch (page) {
      case 'contracts':
        fetchData('/contracts', setContracts);
        break;
      case 'settlements':
        fetchData('/settlements', setSettlements);
        break;
      case 'transactions':
        fetchData('/transactions', setTransactions);
        break;
      case 'artifacts':
        fetchData('/artifacts', setArtifacts);
        break;
      case 'demo':
        fetchData('/contracts', setContracts);
        break;
      default:
        break;
    }
  };

  return (
    <div className="app-container">
      <NavBar onViewChange={handleViewChange} />
      <div className="detail-page">
        {displayPage === 'contracts' && <ContractsPage contracts={contracts} />}
        {displayPage === 'settlements' && <SettlementsPage settlements={settlements} />}
        {displayPage === 'transactions' && <TransactionsPage transactions={transactions} />}
        {displayPage === 'artifacts' && <ArtifactsPage artifacts={artifacts} />}
        {displayPage === 'demonstration' && <DemoPage contracts={contracts} />}
      </div>
    </div> 
  );
};

export default App;
