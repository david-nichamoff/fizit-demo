import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import fizitLogo from '../static/assets/logo/fizit_white-gray.png';
import Contracts from './components/Contracts';
import HowItWorks from './components/HowItWorks';
import AboutUs from './components/AboutUs';
import Careers from './components/Careers';
import Industries from './components/Industries';
import Resources from './components/Resources';
import Quote from './components/Quote';
import Cookies from 'js-cookie';

const App = () => {
  const [contracts, setContracts] = useState([]);
  const [user, setUser] = useState(null);
  const [activePage, setActivePage] = useState('HowItWorks');

  useEffect(() => {
    fetchUser();
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get('/user/', { withCredentials: true });
      setUser(response.data);
      fetchData('/contracts', setContracts);
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };

  const fetchData = async (url, setData) => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL}${url}`, {
        withCredentials: true,
      });
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

  const handleLogout = async () => {
    try {
      const csrfToken = Cookies.get('csrftoken');
      await axios.post('/logout/', null, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        withCredentials: true,
      });
      setUser(null);
      setActivePage('HowItWorks');
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

  const renderPage = () => {
    switch (activePage) {
      case 'HowItWorks':
        return <HowItWorks />;
      case 'Resources':
        return <Resources />;
      case 'Industries':
        return <Industries />;
      case 'AboutUs':
        return <AboutUs />;
      case 'Quote':
        return <Quote />;
      case 'Contracts':
        return <Contracts contracts={contracts} user={user} />;
      default:
        return <HowItWorks />;
    }
  };

  return (
    <div className="app-container">
      <div className="title-bar">
        <img src={fizitLogo} alt="FIZIT Logo" className="logo" />
        <nav className="nav-links">
          <a href="#" onClick={() => setActivePage('HowItWorks')}>How it Works</a>
          <a href="#" onClick={() => setActivePage('Resources')}>Resources</a>
          <a href="#" onClick={() => setActivePage('Industries')}>Industries</a>
          <a href="#" onClick={() => setActivePage('AboutUs')}>About Us</a>
          <a href="#" onClick={() => setActivePage('Quote')}>Request a Quote</a>
          {user && <a href="#" className="contracts-link" onClick={() => setActivePage('Contracts')}>Contracts</a>}
        </nav>
        {user ? (
          <div className="user-dropdown">
            <span>Hello, {user.first_name}</span>
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
      <div className="content-section">
        {renderPage()}
      </div>
      <div className="footer-bar">
        <div className="footer-column">
          <h3>Industries</h3>
          <a href="#">Offshore Drilling</a>
          <a href="#">Wastewater</a>
          <a href="#">Construction</a>
        </div>
        <div className="footer-column">
          <h3>Product</h3>
          <a href="#">How it Works</a>
          <a href="#">Ambassador Program</a>
          <a href="#">Technology</a>
        </div>
        <div className="footer-column">
          <h3>Resources</h3>
          <a href="#">Press Room</a>
          <a href="#">Whitepapers</a>
          <a href="#">Videos and Podcasts</a>
        </div>
        <div className="footer-column">
          <h3>About Us</h3>
          <a href="#">Our Team</a>
          <a href="#">Partners</a>
          <a href="#">Careers</a>
        </div>
        <div className="footer-column">
          <h3>Follow Us</h3>
          <a href="#">X</a>
          <a href="#">LinkedIn</a>
          <a href="#">YouTube</a>
          <a href="#">Instagram</a>
          <a href="#">Facebook</a>
        </div>
      </div>
      <div className="footer-bottom">
        <img src={fizitLogo} alt="FIZIT Logo" className="footer-logo" />
        <p>©2024 by FIZIT, Inc.</p>
      </div>
    </div>
  );
};

export default App;