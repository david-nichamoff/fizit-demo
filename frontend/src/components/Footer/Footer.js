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
          <NavItem className="instance-node" status="default" text="How It Works" type="reverse" to="/how-it-works" />
          <NavItem className="instance-node" status="default" text="Why Fizit" type="reverse" to="/why-fizit" />
          <NavItem className="instance-node" status="default" text="Get a Quote" type="reverse" to="/get-a-quote" />
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