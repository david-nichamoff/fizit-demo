import React, { useEffect, useState } from "react";
import fizitLogo from "../../../static/assets/logo/fizit_full_color.png"; // Adjust path if necessary


const FIZITHome = () => {
  const [transactionCount, setTransactionCount] = useState(0);

  useEffect(() => {
    // Simulating transaction count animation
    let start = 0;
    let end = 500000; 
    let duration = 10000;
    let stepTime = duration / (end - start);

    const incrementCounter = () => {
      if (start < end) {
        start += Math.ceil(end / 100);
        setTransactionCount(start);
        setTimeout(incrementCounter, stepTime);
      } else {
        setTransactionCount(end);
      }
    };

    incrementCounter();
  }, []);

  return (
    <div style={styles.container}>
      <img src={fizitLogo} alt="FIZIT Logo" style={styles.logo} />
      <h1 style={styles.title}>It's Your Money and Timing is Everything</h1>
      <p style={styles.subtitle}>
        FIZIT empowers you to optimize cash flow with cutting-edge IoT and blockchain technology
      </p>

      <p style={styles.detail}>
        FIZIT has Paid:
      </p>
      <div style={styles.counterContainer}>
       ${transactionCount.toLocaleString()}
      </div>
      <p style={styles.detail}>
        To Customers Next Day for Value Delivered
      </p>

      <a href="mailto:info@fizit.biz" style={styles.contactButton}>
        Contact Us
      </a>

      <div style={styles.footer}>&copy; {new Date().getFullYear()} FIZIT, Inc. All rights reserved.</div>
    </div>
  );
};

// Simple inline styles
const styles = {
  container: {
    textAlign: "center",
    fontFamily: "Arial, sans-serif",
    padding: "50px 20px",
  },
  logo: {
    width: "250px", 
    height: "auto", 
    marginBottom: "20px",
  },
  title: {
    fontSize: "2rem",
    fontWeight: "bold",
    color: "#2c3e50",
  },
  subtitle: {
    margin: "20px 0",
    marginBottom: "60px",
    fontSize: "1.2rem",
    color: "#555",
  },
  detail: {
    margin: "20px 0",
    fontSize: "1rem",
    color: "#555",
  },
  counterContainer: {
    display: "inline-block",
    backgroundColor: "#222", // Dark background like a scoreboard
    color: "#FFD700", // Gold/yellow numbers for contrast
    padding: "20px 30px",
    marginTop: "0px",
    borderRadius: "8px",
    fontFamily: "'Orbitron', sans-serif", 
    fontSize: "3rem", 
    fontWeight: "bold",
    letterSpacing: "5px",
    boxShadow: "0px 4px 8px rgba(0,0,0,0.3)", // Slight shadow for depth
  },
  contactButton: {
    display: "inline-block",
    marginTop: "40px",
    padding: "12px 24px",
    fontSize: "1.2rem",
    fontWeight: "bold",
    color: "#fff",
    backgroundColor: "rgba(107, 72, 255, 1)",
    border: "none",
    borderRadius: "8px",
    textDecoration: "none",
    transition: "background-color 0.3s",
    cursor: "pointer",
  },
  footer: {
    marginTop: "20px",
    fontSize: "0.9rem",
    color: "#777",
  },
};

export default FIZITHome;