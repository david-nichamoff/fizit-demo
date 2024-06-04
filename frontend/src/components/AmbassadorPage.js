import React from 'react';
import uc from '../assets/image/under_construction_pc_800_wht.jpg'; 
import './DevicesPage.css';

const DevicesPage = () => {
  return (
    <div className="devices-page">
      <div className="under-construction-container">
        <h2>Ambassador Program</h2>
        <img src={uc} alt="Under Construction" className="uc" />
      </div>
    </div>
  );
};

export default DevicesPage;