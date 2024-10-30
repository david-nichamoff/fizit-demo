import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Footer } from "../../components/Footer/Footer";
import { Header } from "../../components/Header/Header";
import { Button } from "../../components/Button/Button";

import sellerImage from "../../../static/assets/image/for_sellers.png";

import "./ForSellers.css";

export const ForSellers = () => {
  const navigate = useNavigate()
  return (
    <div className="for-sellers">
      <Header loginState="default" />
      <div className="for-sellers-columns">
        <div className="for-sellers-left">
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
          <div className="seller-image">
            <img className="seller" alt="seller" src={sellerImage} />
          </div>
        </div>
        <div className="for-sellers-right">
          <div className="quote-container">
            <p className="quote-text">
            “Growth requires capital, and my customers have my money.” 
            </p>
            <p className="attribution-text">
              Owner, Oilfield Services Company
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

export default ForSellers;