import React from "react";
import PropTypes from "prop-types";
import { NavLink } from "react-router-dom";
import "./NavItem.css";

export const NavItem = ({
  className = "",
  divClassName = "",
  status = "default",
  text,
  type = "regular",
  to,
  onClick,
  children,
  size = "regular"
}) => {
  return (
    <div className="nav-item-container" onClick={onClick}>
      <NavLink
        to={to}
        className={({ isActive }) => `${className} ${isActive ? "active-link" : ""}`}
      >
        {({ isActive }) => (
          <div className={`nav-item ${divClassName} ${status} ${type} ${size} ${isActive ? "active" : ""}`}>
            {text}
          </div>
        )}
      </NavLink>
      {children && (
        <div className="dropdown-content">
          {children}
        </div>
      )}
    </div>
  );
};

NavItem.propTypes = {
  className: PropTypes.string,
  divClassName: PropTypes.string,
  status: PropTypes.string,
  text: PropTypes.string.isRequired,
  type: PropTypes.string,
  to: PropTypes.string.isRequired,
  onClick: PropTypes.func,
  children: PropTypes.node,
  size: PropTypes.oneOf(["small", "regular"])
};

export default NavItem;