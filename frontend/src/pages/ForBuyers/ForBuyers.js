import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Footer } from "../../components/Footer/Footer";
import { Header } from "../../components/Header/Header";

import avalancheImage from "../../../static/assets/image/avalanche.png";
import cashImage from "../../../static/assets/image/cash.png";

import "./ForBuyers.css";

export const ForBuyers = () => {
  const navigate = useNavigate()
  return (
    <div className="why-fizit">
      <Header loginState="default" />
      <div className="blade">
        <div className="hero-container">
          <div className="hero-grid">
            <div className="hero-frame">
              <div className="hero-text-frame">
                <p className="hero-heading">Why FIZIT?</p>
                <p className="hero-text">
                  Unlocking Capital Efficiency with FIZIT:<br /> 
                  Extend Your Days Payable Outstanding (DPO)
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="quote-blade">
        <div className="quote-container">
          <p className="quote-text">
            "We need to have best in class DPO of 90+ days, but also need a strong supply chain."
          </p>
          <p className="attribution-text">
            Chief Procurement Officer, Chemical Manufacturer
          </p>
        </div>
      </div>
      <div className="blade">
        <div className="blade-container">
          <div className="blade-grid">
            <div className="blade-frame">
              <div className="blade-text-frame">
                <p className="blade-heading">Manage Cash Flow Effectively</p>
                <p className="blade-text">
                In today's fast-paced business environment, cash flow is more 
                than just an indicator of financial health—it's the very pulse 
                of your business. At FIZIT, we understand that managing cash 
                flow effectively means leveraging every opportunity to optimize 
                your working capital. The same technology and financial 
                infrastructure used to pay companies faster also enables delayed 
                payments, giving you the strategic advantage to significantly 
                increase your DPO and take control of your cash flow, empowering 
                you in your financial decision-making.
                </p>
              </div>
            </div>
          </div>
          <div className="cash-image">
            <img className="cash" alt="cash" src={cashImage} />
          </div>
        </div>
      </div>
      <Footer loginState="default" />
    </div>
  );
};

export default ForBuyers;