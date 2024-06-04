import React from 'react';
import logo from '../assets/logo/fizit_white-gray.png'; 
import '../App.css'; 

const NavBar = ({ onViewChange }) => {
  return (
    <nav className="nav-bar">
      <div className="logo">
        <img src={logo} alt="Fizit Logo" className="logo" />
      </div>
      <ul className="nav-links">
        <li>
          <button onClick={() => onViewChange('contracts')}>Contracts</button>
        </li>
        <li>
          <button onClick={() => onViewChange('settlements')}>Settlements</button>
        </li>
        <li>
          <button onClick={() => onViewChange('transactions')}>Transactions</button>
        </li>
        <li>
          <button onClick={() => onViewChange('tickets')}>Tickets</button>
        </li>
        <li>
          <button onClick={() => onViewChange('devices')}>Devices</button>
        </li>
        <li>
          <button onClick={() => onViewChange('artifacts')}>Artifacts</button>
        </li>
        <li>
          <button onClick={() => onViewChange('payments')}>Payments</button>
        </li>
        <li>
          <button onClick={() => onViewChange('deposits')}>Deposits</button>
        </li>
        <li>
          <button onClick={() => onViewChange('ambassador')}>Ambassador</button>
        </li>
        <li>
          <button onClick={() => onViewChange('administration')}>Admin</button>
        </li>
      </ul>
    </nav>
  );
};

export default NavBar;
