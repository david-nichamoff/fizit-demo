import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Multiselect from 'multiselect-react-dropdown';
import Cookies from 'js-cookie';
import { formatCurrency, formatDate } from './Utils';
import './TicketsPage.css';

const TicketsPage = ({ contracts }) => {
  const [selectedContracts, setSelectedContracts] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [selectedTickets, setSelectedTickets] = useState([]);
  const [dateFrom, setDateFrom] = useState(new Date().toISOString().slice(0, 10));
  const [dateTo, setDateTo] = useState(new Date().toISOString().slice(0, 10));
  const [noTicketsFound, setNoTicketsFound] = useState(false);

  const handleGetTickets = async () => {
    try {
      const ticketResponses = await Promise.all(
        selectedContracts.map((contract) =>
          axios.get(`${process.env.REACT_APP_API_URL}/contracts/${contract}/tickets`, {
            params: { start_date: dateFrom, end_date: dateTo }
          })
        )
      );
      const allTickets = ticketResponses.flatMap(response => response.data);
      setTickets(allTickets);
      setNoTicketsFound(allTickets.length === 0);
    } catch (error) {
      console.error('Error fetching tickets:', error);
    }
  };

  const handleTicketSelect = (ticket) => {
    setSelectedTickets((prevSelectedTickets) => {
      if (prevSelectedTickets.includes(ticket)) {
        return prevSelectedTickets.filter((t) => t !== ticket);
      } else {
        return [...prevSelectedTickets, ticket];
      }
    });
  };

  const handleProcessTickets = async () => {
    try {
      const csrfToken = Cookies.get('csrftoken');
      await Promise.all(
        selectedTickets.map((ticket) => {
          const jsonPayload = [
            {
              extended_data: { "ticket_id": ticket.ticket_id },
              transact_dt: new Date(ticket.approved_dt).toISOString(),
              transact_data: { "ticket_amt": ticket.ticket_amt }
            }
          ];
          console.log("JSON to be sent:", JSON.stringify(jsonPayload)); // Logging for debugging
          return axios.post(
            `${process.env.REACT_APP_API_URL}/contracts/${ticket.contract_idx}/transactions/`,
            JSON.stringify(jsonPayload),
            {
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
              }
            }
          );
        })
      );
      alert('Tickets processed successfully.');
      setSelectedTickets([]);
    } catch (error) {
      console.error('Error processing tickets:', error);
      alert('Error processing tickets.');
    }
  };

  return (
    <div className="detail-page">
      <div className="filter-container">
        <h2>Tickets</h2>
        <div className="multiselect-container">
          <Multiselect
            options={contracts.map((contract) => ({
              key: contract.contract_name,
              value: contract.contract_idx
            }))}
            selectedValues={selectedContracts.map((contract) => ({
              key: contracts.find((c) => c.contract_idx === contract)?.contract_name,
              value: contract
            }))}
            onSelect={(selectedList) => setSelectedContracts(selectedList.map((item) => item.value))}
            onRemove={(selectedList) => setSelectedContracts(selectedList.map((item) => item.value))}
            displayValue="key"
            placeholder="Select contracts..."
            style={{ maxHeight: '200px', overflow: 'auto' }}
          />
        </div>
        <div className="date-filters">
          <label htmlFor="dateFrom">Date From:</label>
          <input type="date" id="dateFrom" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} required />
          <label htmlFor="dateTo">Date To:</label>
          <input type="date" id="dateTo" value={dateTo} onChange={(e) => setDateTo(e.target.value)} required />
          <button
            onClick={handleGetTickets}
            className={`apply-filter-button ${selectedContracts.length === 0 || !dateFrom || !dateTo ? 'disabled' : ''}`}
            disabled={selectedContracts.length === 0 || !dateFrom || !dateTo}
          >
            Get Tickets
          </button>
          {noTicketsFound && (
            <span className="no-tickets-found">
              No tickets found
            </span>
          )}
        </div>
      </div>

      {tickets.length > 0 && (
        <div className="ticket-container">
          <div className="ticket-header">
            <div className="column-header string-column">Contract</div>
            <div className="column-header number-column">Ticket ID</div>
            <div className="column-header date-column">Approved Date</div>
            <div className="column-header amount-column">Ticket Amount</div>
          </div>
          <ul className="ticket-list">
            {tickets.map((ticket, index) => (
              <li 
                key={index} 
                className={`ticket-item ${selectedTickets.includes(ticket) ? 'selected' : ''}`}
                onClick={() => handleTicketSelect(ticket)}
              >
                <div className="ticket-column string-column">{ticket.contract_name}</div>
                <div className="ticket-column number-column">{ticket.ticket_id}</div>
                <div className="ticket-column date-column">{formatDate(ticket.approved_dt)}</div>
                <div className="ticket-column amount-column">{formatCurrency(ticket.ticket_amt)}</div>
              </li>
            ))}
          </ul>
          <button
            onClick={handleProcessTickets}
            className={`process-tickets-button ${selectedTickets.length === 0 ? 'disabled' : ''}`}
            disabled={selectedTickets.length === 0}
          >
            Process Selected Tickets
          </button>
        </div>
      )}
    </div>
  );
};

export default TicketsPage;