import React from "react";
import PropTypes from "prop-types";

import "./Button.css";
import "../StyleGuide/StyleGuide.css";

export const Button = ({ style, size, className, text, onClick }) => {
  return (
    <div className={`button ${style} ${size} ${className}`} onClick={onClick}>
      <div className="div">
        {text}
      </div>
    </div>
  );
};

Button.propTypes = {
  style: PropTypes.oneOf(["primary", "secondary", "disabled"]),
  size: PropTypes.oneOf(["default", "small"]),
  className: PropTypes.string,
  text: PropTypes.string.isRequired,
  onClick: PropTypes.func, 
};

export default Button;