import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Footer } from "../../components/Footer/Footer";
import { Header } from "../../components/Header/Header";
import { Button } from "../../components/Button/Button";

import buyerImage from "../../../static/assets/image/for_buyers.png";

import "./ForBuyers.css";

export const ForBuyers = () => {
  const navigate = useNavigate()
  return (
    <div className="for-buyers">
      <Header loginState="default" />
      <div className="for-buyers-columns">
        <div className="for-buyers-left">
          <div className="blade">
            <div className="hero-container">
              <div className="hero-grid">
                <div className="hero-frame">
                  <div className="hero-text-frame">
                    <p className="hero-heading">Why FIZIT?</p>
                    <p className="hero-text">
                    It's Your Money and Timing is Everything
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="buyer-image">
            <img className="buyer" alt="buyer" src={buyerImage} />
          </div>
        </div>
        <div className="for-buyers-right">
          <div className="quote-container">
            <p className="quote-text">
            “Lengthening DPO is part of the path  to best-in-class cash conversion cycles.  We’re seeking DPO of 90+ days, while securing a strong supply chain and becoming a customer of choice.”
            </p>
            <p className="attribution-text">
              Chief Procurement Officer, Chemical Manufacturer
            </p>
          </div>
          <div className="button-container">
            <Button
              className="quote-button"
              size="default"
              style="primary"
              text="Contact Us"
              onClick={() => navigate("/get-a-quote")}
            />
          </div>
        </div>
      </div>
      <Footer loginState="default" />
    </div>
  );
};

export default ForBuyers;