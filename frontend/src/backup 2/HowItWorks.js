import React from 'react';
import './HowItWorks.css';
import howItWorks1 from '../../static/assets/how_it_works/how_it_works_1.png';
import howItWorks2 from '../../static/assets/how_it_works/how_it_works_2.png';

const HowItWorks = () => {
  return (
    <div className="how-it-works">
      <h1>How it Works</h1>
      <img src={howItWorks1} alt="How It Works 1" className="how-it-works-image" />
      <div className="how-it-works-text">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
      </div>
      <img src={howItWorks2} alt="How It Works 2" className="how-it-works-image" />
    </div>
  );
};

export default HowItWorks;