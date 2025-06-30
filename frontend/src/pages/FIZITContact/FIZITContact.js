import React from "react";
import "../FIZITHome/FIZITHome.css";  // Reuse existing styles

import fizitLogo from "../../assets/logo/fizit_full_color.png";

const FIZITContact = () => {
  return (
    <div className="container">
      {/* Logo */}
      <div className="logo-container">
        <img src={fizitLogo} alt="FIZIT Logo" className="logo" />
      </div>

      {/* Header */}
      <div className="title-container">
        <h1 className="title">Let’s Talk</h1>
        <p className="subtitle">
          Schedule a meeting with our team or send us a message below.
        </p>
      </div>

      {/* Calendly Embed */}
      <div className="calendly-container" style={{ minHeight: "700px" }}>
        <iframe
          title="Schedule Meeting"
          src="https://calendly.com/andrewbruce/fizit-discovery"
          width="100%"
          height="700"
          frameBorder="0"
          scrolling="no"
          style={{ border: "none", overflow: "hidden" }}
        ></iframe>
      </div>

      {/* Contact Form */}
      <h4 className="section-title">Contact Us Directly</h4>
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

      {/* Footer */}
      <div className="footer">
        &copy; {new Date().getFullYear()} FIZIT, Inc. All rights reserved.
      </div>
    </div>
  );
};

export default FIZITContact;