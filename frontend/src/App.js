import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import fizitLogo from '../static/assets/logo/fizit_white-gray.png';
import Contracts from './components/Contracts';
import GetPaidFaster from './components/GetPaidFaster'; 

const App = () => {
  const [contracts, setContracts] = useState([]);
  const [username, setUsername] = useState(null);

  useEffect(() => {
    fetchData('/contracts', setContracts);
    // Fetch username logic here, setUsername accordingly
  }, []);

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

  const handleLogout = () => {
    console.log('User logged out');
    // Add your logout logic here
  };

  return (
    <div className="app-container">
      <div className="title-bar">
        <img src={fizitLogo} alt="FIZIT Logo" className="logo" />
        <nav className="nav-links">
          <a href="#">How it works</a>
          <a href="#">Resources</a>
          <a href="#">Industries</a>
          <a href="#">Careers</a>
          <a href="#">About us</a>
        </nav>
        {username ? (
          <div className="user-dropdown">
            <span>Hello {username}</span>
            <div className="dropdown-content">
              <button onClick={handleLogout}>Logout</button>
            </div>
          </div>
        ) : (
          <div className="auth-links">
            <a href="/login" className="login-link">Log In</a>
            <a href="/register" className="register-link">Register</a>
          </div>
        )}
      </div>
      <GetPaidFaster /> 
      <div className="contract-scroll-section">
        <Contracts contracts={contracts} />
      </div>
      <div className="footer-bar">
        <div className="footer-column">
          <h3>Account</h3>
          <a href="#">Register</a>
          <a href="#">Login</a>
          <a href="#">Logout</a>
          <a href="#">Get a Quote</a>
          <a href="#">Become an Ambassador</a>
        </div>
        <div className="footer-column">
          <h3>About</h3>
          <a href="#">How FIZIT Works</a>
          <a href="#">Our Story</a>
          <a href="#">Careers</a>
          <a href="#">Contact Us</a>
        </div>
        <div className="footer-column">
          <h3>Resources</h3>
          <a href="#">Help Center</a>
          <a href="#">Press Room</a>
          <a href="#">Whitepapers</a>
        </div>
        <div className="footer-column">
          <h3>Industries</h3>
          <a href="#">Wastewater</a>
          <a href="#">Offshore Drilling</a>
          <a href="#">Construction</a>
        </div>
        <div className="footer-column">
          <h3>Follow Us</h3>
          <a href="#">X</a>
          <a href="#">LinkedIn</a>
          <a href="#">YouTube</a>
          <a href="#">Instagram</a>
        </div>
      </div>
      <div className="footer-bottom">
        <p>©2024 by FIZIT, Inc.</p>
      </div>
    </div>
  );
};

export default App;