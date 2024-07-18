import React from "react";
import PropTypes from "prop-types";

import { Logo } from "../Logo/Logo";
import { NavItem } from "../NavItem/NavItem";
import { useNavigate } from "react-router-dom";

import "./Footer.css";
import "../StyleGuide/StyleGuide.css";

export const Footer = ({ loginState }) => {
  const navigate = useNavigate();

  return (
    <div className={"footer"}>
      <div className="container">
        <div className="nav-left">
          <div onClick={() => navigate("/")}>
            <Logo className="logo-instance" logoType="reverse" />
          </div>
        </div>
        <div className="nav-center">
          <div className="column-header">
            <div className="column-text">How it Works</div>
            <NavItem className="nav-link" status="default" text="How it Works" type="reverse" to="/how-it-works" size='small' />
          </div>
          <div className="column-header">
            <div className="column-text">Why FIZIT?</div>
            <NavItem className="nav-link" status="default" text="For Buyers" type="reverse" to="/for-buyers" size='small' />
            <NavItem className="nav-link" status="default" text="For Sellers" type="reverse" to="/for-sellers" size='small' />
          </div>
          <div className="column-header">
            <div className="column-text">About Us</div>
            <NavItem className="nav-link" status="default" text="Get a Quote" type="reverse" to="/get-a-quote" size='small' />
          </div>
        </div>
      </div>
      <div className="footer-bottom">
        <div className="white-line"></div>
        <p className="copyright-text">© 2024 All rights reserved</p>
      </div>
    </div>
  );
};

Footer.propTypes = {
  loginState: PropTypes.oneOf(["after-login", "default"]),
};

export default Footer;