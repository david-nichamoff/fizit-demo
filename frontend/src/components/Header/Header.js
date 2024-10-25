import React from "react";
import PropTypes from "prop-types"; 
import { useNavigate } from "react-router-dom";

import { Logo } from "../Logo/Logo";
import { NavItem } from "../NavItem/NavItem";

import "./Header.css";
import "../StyleGuide/StyleGuide.css";

export const Header = ({ loginState }) => {
  const navigate = useNavigate();

  return (
    <div className="header">
      <div className="container">
        <div className="nav-left" onClick={() => navigate("/")}>
          <Logo className="logo-instance" logoType="default" />
        </div>
        <div className="nav-center">
          <NavItem className="nav-link" status="default" text="For Buyers" type="regular" to="/for-buyers" />
          <NavItem className="nav-link" status="default" text="For Sellers" type="regular" to="/for-sellers" />
          <NavItem className="nav-link" status="default" text="How it Works" type="regular" to="/how-it-works" />
          <NavItem className="nav-link" status="default" text="Contact Us" type="regular" to="/get-a-quote" />
        </div>
      </div>
    </div>
  );
};

Header.propTypes = {
  loginState: PropTypes.oneOf(["after-login", "default"]),
};

export default Header;