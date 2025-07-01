import React from "react";
import "../FIZITHome/FIZITHome.css";  // Reuse existing styles

import fizitLogo from "../../assets/logo/fizit_full_color.png";

const FIZITContact = () => {
  return (
    <div className="container">
      {/* Header */}
      <div className="title-container">
        <h1 className="title">Let’s Talk</h1>
        <p className="subtitle">
          Schedule a meeting with our team today
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

      {/* Footer */}
      <div className="footer">
        &copy; {new Date().getFullYear()} FIZIT, Inc. All rights reserved.
      </div>
    </div>
  );
};

export default FIZITContact;