import React, { useState, useEffect } from 'react';
import axios from 'axios';
import logo from '../../static/assets/logo/fizit_white-gray.png';
import '../App.css';
import Cookies from 'js-cookie';

const NavBar = ({ onViewChange }) => {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await axios.get('/user/');
        setUser(response.data);
      } catch (error) {
        console.error('Error fetching user:', error);
      }
    };

    fetchUser();
  }, []);

  const handleLogout = async () => {
    try {
      const csrfToken = Cookies.get('csrftoken');
      await axios.post('/logout/', null, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
      });
      window.location.href = '';
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

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
          <button onClick={() => onViewChange('artifacts')}>Artifacts</button>
        </li>
        <li>
          <button onClick={() => onViewChange('payments')}>Payments</button>
        </li>
        <li>
          <button onClick={() => onViewChange('deposits')}>Deposits</button>
        </li>
      </ul>
      <div className="user-info">
        {user ? (
          <>
            <span className="username">{user.username}</span>
            <button onClick={handleLogout} className="logout-link">Logout</button>
          </>
        ) : (
          <a href="/login/">Login</a>
        )}
      </div>
    </nav>
  );
};

export default NavBar;