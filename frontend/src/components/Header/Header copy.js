import React, { useState } from "react";
import PropTypes from "prop-types";
import { useNavigate, useLocation } from "react-router-dom";

import { Logo } from "../Logo/Logo";
import { NavItem } from "../NavItem/NavItem";

import "./Header.css";
import "../StyleGuide/StyleGuide.css";

export const Header = ({ loginState }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleDropdownToggle = (event) => {
    event.stopPropagation();
    setDropdownOpen((prev) => !prev);
  };

  const handleMouseEnter = () => {
    setDropdownOpen(true);
  };

  const handleMouseLeave = () => {
    setDropdownOpen(false);
  };

  const isWhyFizitActive = location.pathname === "/for-buyers" || location.pathname === "/for-sellers";

  return (
    <div className="header">
      <div className="container">
        <div className="nav-left" onClick={() => navigate("/")}>
          <Logo className="logo-instance" logoType="default" />
        </div>
        <div className="nav-center">
          <NavItem className="nav-link" status="default" text="How it Works" type="regular" to="/how-it-works" />
          <div
            className={`dropdown ${dropdownOpen ? "open" : ""}`}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          >
            <div 
              className={`nav-link ${isWhyFizitActive ? "active" : ""}`} 
              onClick={handleDropdownToggle}
            >
              Why FIZIT?
            </div>
            <div className="dropdown-content">
              <NavItem className="nav-link" status="default" text="For Buyers" type="regular" to="/for-buyers" />
              <NavItem className="nav-link" status="default" text="For Sellers" type="regular" to="/for-sellers" />
            </div>
          </div>
          <NavItem className="nav-link" status="default" text="Get a Quote" type="regular" to="/get-a-quote" />
        </div>
      </div>
    </div>
  );
};

Header.propTypes = {
  loginState: PropTypes.oneOf(["after-login", "default"]),
};

export default Header;