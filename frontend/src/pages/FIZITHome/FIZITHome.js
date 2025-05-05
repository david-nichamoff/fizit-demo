import React, { useEffect, useState } from "react";
import "./FIZITHome.css";

// Static assets
import fizitLogo from "../../assets/logo/fizit_full_color.png"; 
import avalancheLogo from "../../assets/logo/PoweredbyAvalanche_RedWhite1.png"; 
import usBankLogo from "../../assets/logo/U.S._Bancorp_logo.png";
import blizzardLogo from "../../assets/logo/BlizzardLogo.jpeg";

const API_URL = "/api/stats/";

const FIZITHome = () => {
  const [transactionValue, setTransactionValue] = useState(0);
  const [endValue, setEndValue] = useState(null);
  const [totalTransactions, setTotalTransactions] = useState(0);

  useEffect(() => {
    const fetchTransactionValue = async () => {
      try {
        const response = await fetch(API_URL);
        const data = await response.json();

        if (data) {
          if (data.total_advance_amt) setEndValue(data.total_advance_amt);
          if (data.total_transactions) setTotalTransactions(data.total_transactions);
        }
      } catch (error) {
        console.error("Error fetching transaction value:", error);
      }
    };

    fetchTransactionValue();
  }, []);

  useEffect(() => {
    if (endValue === null) return;

    let start = 0;
    const duration = 5000;
    const stepTime = duration / (endValue - start);

    const incrementCounter = () => {
      if (start < endValue) {
        start += Math.ceil(endValue / 100);
        setTransactionValue(start);
        setTimeout(incrementCounter, stepTime);
      } else {
        setTransactionValue(endValue);
      }
    };

    incrementCounter();
  }, [endValue]);

  return (
    <div className="container">

      <div className = "logo-container">
        <img src={fizitLogo} alt="FIZIT Logo" className="logo" />
      </div>

      <div className = "title-container">
        <h1 className="title">It's Your Money and Timing is Everything</h1>
        <p className="subtitle">
          FIZIT empowers you to optimize cash flow with cutting-edge IoT and blockchain technology
        </p>
      </div>

      <div className = "counter-container">
        <p className="body">
          FIZIT has funded {totalTransactions.toLocaleString()} transactions totaling:
        </p>
        <div className="counter">
          ${transactionValue.toLocaleString()}
        </div>
        <p className="body">Get Paid Tomorrow for Value Delivered Today</p>
      </div>

      <h4 className="section-title">Partners</h4>
      <div className="partner-container">
        <img src={avalancheLogo} alt="Avalanche Logo" className="partner-logo" />
        <img src={usBankLogo} alt="USBank Logo" className="partner-logo" />
      </div>

      <h4 className="section-title">Investors</h4>
      <div className="partner-container">
        <img src={blizzardLogo} alt="Blizzard Logo" className="partner-logo" />
      </div>

      {/* Contact Form */}
      <h4 className="section-title">Contact Us</h4>
      <form 
        action="https://formspree.io/f/xoveqrro"
        method="POST" 
        className="contact-form"
      >
        <div className="form-group">
          <label htmlFor="name" className='label'>Name: </label>
          <input type="text" name="name" id="name" required />
        </div>
        <div className="form-group">
            <label htmlFor="email" className='label'>Email: </label>
            <input type="email" name="email" id="email" required />
        </div>
        <div className="form-group">
            <label htmlFor="message" className='label'>Message: </label>
            <textarea name="message" id="message" rows="4" required />
        </div>
        <button type="submit" className="message-button">Send Message</button>
      </form>

      <div className="footer">
        &copy; {new Date().getFullYear()} FIZIT, Inc. All rights reserved.
      </div>
    </div>

  );
};

export default FIZITHome;