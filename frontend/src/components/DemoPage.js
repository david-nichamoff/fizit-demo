import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Cookies from 'js-cookie';
import './DemoPage.css';

const DemoPage = ({ contracts }) => {
  const [selectedContract, setSelectedContract] = useState('');
  const [extId, setExtId] = useState(JSON.stringify({ ticket_no: 1000 }, null, 2));
  const [transactDt, setTransactDt] = useState('');
  const [transactData, setTransactData] = useState(JSON.stringify({ ticket_amt: 500 }, null, 2));
  const [isFormValid, setIsFormValid] = useState(false);

  useEffect(() => {
    const contract = contracts.find((contract) => contract.contract_name === selectedContract);
    if (contract) {
      setIsFormValid(true);
    } else {
      setIsFormValid(false);
    }
  }, [selectedContract, contracts]);

  const handleContractChange = (e) => {
    setSelectedContract(e.target.value);
  };

  const handlePayMeNow = async () => {
    try {
      const contract = contracts.find((contract) => contract.contract_name === selectedContract);
      if (contract) {
        const csrfToken = Cookies.get('csrftoken');
        const jsonPayload = [{ext_id: JSON.parse(extId), transact_dt: new Date(transactDt).toISOString(), transact_data: JSON.parse(transactData)}]; 
        console.log("JSON to be sent:", JSON.stringify(jsonPayload));


        const response = await axios.post(
          `/api/contracts/${contract.contract_idx}/transactions/`,
          JSON.stringify(jsonPayload),
          {
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken,
            }
          }
        );

        alert('Transaction successful!');
      } else {
        alert('Contract not found.');
      }
    } catch (error) {
      console.error('Error during transaction:', error);
      alert('Transaction failed.');
    }
  };

  return (
    <div className="demo-page">
      <div className="paymenow-container">
        <h2>Pay Me Now</h2>
        <div className="form-group">
          <label htmlFor="contractName">Contract Name:</label>
          <select id="contractName" value={selectedContract} onChange={handleContractChange}>
            <option value="">Select a contract</option>
            {contracts.map((contract, index) => (
              <option key={index} value={contract.contract_name}>{contract.contract_name}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="extId">External ID:</label>
          <textarea
            id="extId"
            value={extId}
            onChange={(e) => setExtId(e.target.value)}
            style={{ height: '60px' }} 
          />
        </div>
        <div className="form-group">
          <label htmlFor="transactDt">Transaction Date:</label>
          <input
            type="datetime-local"
            id="transactDt"
            value={transactDt}
            onChange={(e) => setTransactDt(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label htmlFor="transactData">Transaction Data:</label>
          <textarea
            id="transactData"
            value={transactData}
            onChange={(e) => setTransactData(e.target.value)}
            style={{ height: '60px' }} 
          />
        </div>
        <button
          onClick={handlePayMeNow}
          disabled={!isFormValid}
          className={isFormValid ? '' : 'disabled'}
        >
          Pay Me Now
        </button>
      </div>
    </div>
  );
};

export default DemoPage;
