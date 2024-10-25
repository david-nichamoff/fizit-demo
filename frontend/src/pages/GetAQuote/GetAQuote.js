import React, { useState } from "react";

import { Footer } from "../../components/Footer/Footer";
import { Header } from "../../components/Header/Header";

import "./GetAQuote.css";

export const GetAQuote = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    message: "",
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  };
  
  const csrftoken = getCookie("csrftoken");
  
  const handleSubmit = (e) => {
    e.preventDefault();
    console.log("Form data being sent:", formData);
  
    fetch("/api/contacts/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken, // Add the CSRF token header
      },
      body: JSON.stringify(formData),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        console.log("Response data:", data); // Log the full response data
        if (data.contact_idx) {
          alert("Thank you for your interest in FIZIT. We will contact you soon.");
          setFormData({
            name: "",
            email: "",
            company: "",
            message: "",
          });
        } else {
          alert("There was an error. Please try again.");
        }
      })
      .catch((error) => {
        console.error("Error sending form data:", error);
      });
  };

  return (
    <div className="quote">
      <Header loginState="default" />
      <div className="right-blade">
        <div className="right-container">
          <p className="right-header">
            FIZIT is right when…
          </p>
          <p className="right-text">
            Delivery is confirmed electronically<br/>
          </p>
          <p className="right-text">
            Access to digital delivery information is available<br />
          </p>
          <p className="right-text">
            Buy/sell contracts are unambiguous<br />
          </p>
          <p className="right-text">
            Invoicing frequency is monthly or more, or on-delivery
          </p>
        </div>
      </div>
      <div className="quote-container">
        <h1>Contact Us</h1>
        <form onSubmit={handleSubmit} className="quote-form">
          <div className="form-group">
            <label htmlFor="name">Name</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="company">Company</label>
            <input
              type="text"
              id="company"
              name="company"
              value={formData.company}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label htmlFor="message">Message</label>
            <textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleChange}
              required
            />
          </div>
          <button
            type="submit"
            className="submit-button"
          >
            Submit
          </button>
        </form>
      </div>
      <Footer loginState="default" />
    </div>
  );
};

export default GetAQuote;