import React from "react";
import PropTypes from "prop-types";
import "./Logo.css";

export const Logo = ({ className, logoType }) => {
  const logoSrc = logoType === "reverse" 
    ? "../../../static/assets/logo/fizit_white-gray.png"
    : "../../../static/assets/logo/fizit_full_color.png";

  return (
    <img className={className} src={logoSrc} alt="Logo" />
  );
};

Logo.propTypes = {
  className: PropTypes.string,
  logoType: PropTypes.oneOf(["default", "reverse"]).isRequired,
};

Logo.defaultProps = {
  logoType: "default",
};

export default Logo;