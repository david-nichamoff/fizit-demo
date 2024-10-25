import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Footer } from "../../components/Footer/Footer";
import { Header } from "../../components/Header/Header";

import iotImage from "../../../static/assets/image/iot.png";
import proofImage from "../../../static/assets/image/proof.png";
import trustImage from "../../../static/assets/image/trust.png";
import flowImage from "../../../static/assets/image/simple_flow.png";

import "./HowItWorks.css";

export const HowItWorks = () => {
  return (
    <div className="how-it-works">
      <Header loginState="default" />
      <div className="blade">
        <div className="blade-container">
          <div className="blade-grid">
            <div className="blade-frame">
              <div className="blade-text-frame">
                <p className="blade-heading">
                As simple as buying gas…FIZIT is the flex you need to optimize cash flow
                </p>
              </div>
            </div>
          </div>
          <div className="flow-image">
            <img className="flow" alt="flow" src={flowImage} />
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
                There is no need to change your existing field automation systems.  From sensors to electronic meters and ticketing systems, FIZIT uses your systems to electronically confirm delivery of goods and services and initiate immediate payment.
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
                <p className="blade-heading">Use Proof of Value</p>
                <p className="blade-text">
                Combining IoT and Electronic Smart Contracts, FIZIT converts proof of delivery into proof of value and calculates the payment due.  This electronic tie virtually eliminates the checking and cross-checking in today’s invoice and payment processes.  
                  <br />
                  <br />
                FIZIT employs the same approach and technologies the world’s largest corporations have used to streamline processes, increase speed, and reduce errors .  Automated transactions, such as these have proved to be 98% accurate with the 2% resoled in the field before the back office even knows about it.  
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
                Step-by-step, the details of each transaction are stored in an immutable shared ledger.  Buyers and sellers see the same unalterable information thus establishing trust and transparency.
                  <br />
                  <br />
                Linking delivery to value to payment without complicated and time-consuming invoice processes, optimizes cash flow,  reduces opportunities for error and fraud, and establishes a clear audit trail.
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