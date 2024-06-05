import React from 'react';
import uc from '../../static/assets/image/under_construction_pc_800_wht.jpg'; 
import './MetersPage.css';

const MetersPage = () => {
  return (
    <div className="devices-page">
      <div className="under-construction-container">
        <h2>Administration</h2>
        <img src={uc} alt="Under Construction" className="uc" />
      </div>
    </div>
  );
};

export default MetersPage;