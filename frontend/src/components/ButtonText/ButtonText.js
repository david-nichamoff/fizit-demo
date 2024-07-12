import React from 'react';
import PropTypes from 'prop-types';

import './ButtonText.css';
import "../StyleGuide/StyleGuide.css";

export const ButtonText = ({ divClassName, riArrowDownLine, size, text, onClick }) => {
  return (
    <div className={`button-text ${size}`} onClick={onClick}>
      <div className={`text-wrapper ${divClassName}`}>
        {text}
      </div>
      <img className="ri-arrow-down-line" src={riArrowDownLine} alt="Arrow Down" />
    </div>
  );
};

ButtonText.propTypes = {
  divClassName: PropTypes.string,
  riArrowDownLine: PropTypes.string,
  size: PropTypes.oneOf(['small', 'default']),
  text: PropTypes.string.isRequired,
  onClick: PropTypes.func,
};

export default ButtonText;