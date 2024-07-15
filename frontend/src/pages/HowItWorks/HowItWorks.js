import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Footer } from "../../components/Footer/Footer";
import { Header } from "../../components/Header/Header";

import personImage from "../../../static/assets/image/woman.png";
import chartImage from "../../../static/assets/image/contracts_chart.png";
import iotImage from "../../../static/assets/image/iot.png";
import proofImage from "../../../static/assets/image/proof.png";
import trustImage from "../../../static/assets/image/trust.png";

import "./HowItWorks.css";

export const HowItWorks = () => {
  return (
    <div className="how-it-works">
      <Header loginState="default" />
      <div className="blade">
        <div className="hero-container">
          <div className="hero-grid">
            <div className="hero-frame">
              <div className="hero-text-frame">
                <p className="hero-heading">How Does it Work?</p>
              </div>
            </div>
          </div>
          <div className="hero-image">
            <img className="person" alt="Person" src={personImage} />
            <img className="chart" alt="Chart" src={chartImage} />
          </div>
        </div>
      </div>
      <div className="blade">
        <div className="blade-container">
          <div className="blade-grid">
            <div className="blade-frame">
              <div className="blade-text-frame">
                <p className="blade-heading">Use Existing IoT Devices</p>
                <p className="blade-text">
                  There has been an explosion in the availability of Internet 
                  of Things (IoT) devices used in industrial processes. Companies 
                  use these devices primarily for measurement, safety, and control. 
                  The solution to today’s inefficiency is to go to the operational 
                  devices and use them as proof of delivery (just like our gas pump 
                  example).
                </p>
              </div>
            </div>
          </div>
          <div className="iot-image">
            <img className="iot" alt="iot" src={iotImage} />
          </div>
        </div>
      </div>
      <div className="blade">
        <div className="blade-container">
          <div className="blade-grid">
            <div className="blade-frame">
              <div className="blade-text-frame">
                <p className="blade-heading">Use Proof of Delivery</p>
                <p className="blade-text">
                  We use the proof of delivery and the existing commercial 
                  contract between the buyer and seller to calculate payment 
                  due. We don't need to wait a month for some checker to check 
                  if the delivery was accurate. If the devices are good enough 
                  for safety and control, they are good enough for payment. <br />
                  <br />
                  The world's largest companies have proven this theory through 
                  the confirmation of hundreds of millions of dollars' worth of 
                  transactions. These automated transactions have proved to be 
                  98% accurate. Even better news: the team on the ground resolves 
                  the 2% of issues, rather than a team in an office removed from 
                  the operation.
                </p>
              </div>
            </div>
          </div>
          <div className="blade-image">
            <img className="proof" alt="Proof" src={proofImage} />
          </div>
        </div>
      </div>
      <div className="blade">
        <div className="blade-container">
          <div className="blade-grid">
            <div className="blade-frame">
              <div className="blade-text-frame">
                <p className="blade-heading">Trust the Transaction</p>
                <p className="blade-text">
                  A shared ledger permanently records the outcomes, ensuring 
                  trust in the transaction since no party can alter it. <br />
                  <br />
                  This process links payment directly to a delivery without 
                  requiring an invoice. It provides a complete audit trail for 
                  all transactions and has undergone testing across multinational 
                  and small-scale businesses. It also has the added benefit of 
                  removing opportunities for fraud.
                </p>
              </div>
            </div>
          </div>
          <div className="trust-image">
            <img className="trust" alt="Trust" src={trustImage} />
          </div>
        </div>
      </div>
      <Footer loginState="default" />
    </div>
  );
};

export default HowItWorks;