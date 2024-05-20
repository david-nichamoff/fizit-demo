import React from 'react';
import logo from '../assets/fizit_white-gray.png'; 
import '../App.css'; 

const NavBar = ({ onViewChange }) => {
  return (
    <nav className="nav-bar">
      <div className="logo">
        <img src={logo} alt="Fizit Logo" className="logo" />
      </div>
      <ul className="nav-links">
        <li>
          <button onClick={() => onViewChange('contracts')}>Overview</button>
        </li>
        <li>
          <button onClick={() => onViewChange('settlements')}>Settlements</button>
        </li>
        <li>
          <button onClick={() => onViewChange('transactions')}>Transactions</button>
        </li>
        <li>
          <button onClick={() => onViewChange('deposits')}>Deposits</button>
        </li>
        <li>
          <button onClick={() => onViewChange('float')}>Float</button>
        </li>
        <li>
          <button onClick={() => onViewChange('ambassador')}>Ambassador</button>
        </li>
        <li>
          <button onClick={() => onViewChange('builder')}>Builder</button>
        </li>
        <li>
          <button onClick={() => onViewChange('artifacts')}>Artifacts</button>
        </li>
        <li>
          <button onClick={() => onViewChange('administration')}>Admin</button>
        </li>
        <li>
          <button onClick={() => onViewChange('demonstration')}>Demo</button>
        </li>
        <li>
          <button onClick={() => onViewChange('documentation')}>API Docs</button>
        </li>
      </ul>
    </nav>
  );
};

export default NavBar;
