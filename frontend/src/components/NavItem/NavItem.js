import React from "react";
import PropTypes from "prop-types";

import { NavLink } from "react-router-dom";

import "./NavItem.css";

export const NavItem = ({ className, divClassName, status, text, type, to }) => {
  return (
    <NavLink to={to} className={({ isActive }) => `${className} ${isActive ? "active" : ""}`}>
      <div className={`nav-item ${divClassName} ${status} ${type}`}>
        {text}
      </div>
    </NavLink>
  );
};

NavItem.propTypes = {
  className: PropTypes.string,
  divClassName: PropTypes.string,
  status: PropTypes.string,
  text: PropTypes.string.isRequired,
  type: PropTypes.string,
  to: PropTypes.string.isRequired, 
};

export default NavItem;