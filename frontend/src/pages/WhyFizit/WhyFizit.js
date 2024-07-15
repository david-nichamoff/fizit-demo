import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Footer } from "../../components/Footer/Footer";
import { Header } from "../../components/Header/Header";
import { Button } from "../../components/Button/Button";

import avalancheImage from "../../../static/assets/image/avalanche.png";
import cashImage from "../../../static/assets/image/cash.png";

import "./WhyFizit.css";

export const WhyFizit = () => {
  const navigate = useNavigate()
  return (
    <div className="why-fizit">
      <Header loginState="default" />
      <div className="blade">
      <div className="hero-container">
          <div className="hero-grid">
            <div className="hero-frame">
              <div className="hero-text-frame">
                <p className="hero-heading">Why Fizit?</p>
                <p className="blade-text">
                  Unlocking Capital Efficiency with FIZIT:<br /> 
                  Extend Your Days Payable Outstanding (DPO)
                </p>
              </div>
            </div>
            <div className="hero-quote-grid">
              <Button
                className="quote-button"
                size="default"
                style="primary"
                text="Get a Free Quote"
                onClick={() => navigate("/get-a-quote")}
              />
            </div>
          </div>
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
      <div className="blade">
        <div className="blade-container">
          <div className="blade-grid">
            <div className="blade-frame">
              <div className="blade-text-frame">
                <p className="blade-heading">How does FIZIT Technology Work?</p>
                <p className="blade-text">
                FIZIT uses smart contract technology to build a legally enforceable 
                relationship between FIZIT and the seller. All IoT readings are 
                stored on chain and provide an auditable record of every delivery
                </p>
              </div>
            </div>
          </div>
          <div className="avalanche-image">
            <img className="avalanche" alt="avalanche" src={avalancheImage} />
          </div>
        </div>
      </div>
      <div className="blade">
        <div className="blade-container one-column">
          <div className="blade-grid">
            <div className="blade-frame">
              <div className="blade-text-frame">
                <p className="blade-heading">Faster Payments</p>
                <p className="blade-text">
                After receiving a reading from a IoT device  or an approved 
                ticket from an Electronic Field Ticketing System, the smart 
                contract calculates the amount due and triggers a request
                for immediate payment.<br />
                <br />
                The seller decides on how it wants to get paid. Payments are 
                made next day for USD bank to bank transfers. Use a digital 
                wallet such as MetaMask or Avalanche Core Wallet for immediate 
                payment using stablecoin.<br />
                <br />
                Depending on payment history, FIZIT can pay anywhere from 80-90% 
                of the value of the deliverable immediately. After FIZIT is paid 
                by the buyer, the remainder is paid by wallet or bank transfer.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      <Footer loginState="default" />
    </div>
  );
};

export default WhyFizit;