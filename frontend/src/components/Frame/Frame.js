import React from "react";
import PropTypes from "prop-types";
import "./Frame.css";

export const Frame = ({ imgSrc, imgAlt, title, text }) => {
  return (
    <div className="frame">
      <img className="icon-container" alt={imgAlt} src={imgSrc} />
      <div className="card">
        <div className="text-wrapper">{title}</div>
        <p className="div">{text}</p>
      </div>
    </div>
  );
};

Frame.propTypes = {
  imgSrc: PropTypes.string.isRequired,
  imgAlt: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  text: PropTypes.string.isRequired,
};

export default Frame;