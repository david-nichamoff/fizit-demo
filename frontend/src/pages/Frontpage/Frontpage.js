import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/Button/Button";
import { ButtonText } from "../../components/ButtonText/ButtonText";
import { Footer } from "../../components/Footer/Footer";
import { Header } from "../../components/Header/Header";
import { Frame } from "../../components/Frame/Frame";

import exchangeIcon from "../../../static/assets/icon/exchange.png";
import monitoringIcon from "../../../static/assets/icon/monitoring.png";
import paymentsIcon from "../../../static/assets/icon/payments.png";
import riArrowDownLineIcon from "../../../static/assets/icon/ri_arrow-down-line.png";
import arrowIcon from "../../../static/assets/icon/arrow.png"; 

import personImage from "../../../static/assets/image/man.png";
import chartImage from "../../../static/assets/image/eps_chart.png";

import getPaidImmediatelyImage from "../../../static/assets/image/get_paid_immediately.png";
import checkersCheckingImage from "../../../static/assets/image/checkers_checking.png";
import retailLearningImage from "../../../static/assets/image/retail_learning.png";

import "./Frontpage.css";

export const Frontpage = () => {
  const navigate = useNavigate();
  const [activeFrame, setActiveFrame] = useState("get-paid-immediately");

  const handleFrameClick = (frame) => {
    setActiveFrame(frame);
  };

  return (
    <div className="frontpage">
      <Header loginState="default" />
      <div className="blade">
        <div className="hero-container">
          <div className="hero-grid">
            <div className="hero-frame">
              <div className="hero-text-frame">
                <p className="hero-heading">Deliver Today, Get Paid Tomorrow</p>
                <p className="hero-text">
                  Fizit uses the latest technologies in IoT, AI and blockchain to provide you the fastest possible
                  payment at the lowest possible cost.
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
              <ButtonText
                className="why-fizit-button"
                divClassName="why-fizit-button"
                riArrowDownLine={riArrowDownLineIcon}
                size="default"
                text="Why Fizit"
                onClick={() => navigate("/why-fizit")}
              />
            </div>
          </div>
          <div className="image-with-chart">
            <img className="person" alt="Person" src={personImage} />
            <img className="chart" alt="Chart" src={chartImage} />
          </div>
        </div>
      </div>
      <div className="blade">
        <div className="accordion-container">
          <p className="blade-text-wrapper">
            Eliminate the Invoicing Process
            </p>
          <div className="accordion-grid">
            <div className="accordion-frame">
              <div
                className={`card-wrapper ${activeFrame === "get-paid-immediately" ? "active" : ""}`}
                onClick={() => handleFrameClick("get-paid-immediately")}
              >
              <div className="card">
                <div className="get-paid-immediately-frame">
                  <div className="get-paid-immediately-text-wrapper">Get Paid Immediately</div>
                    <img className="arrow_icon" alt="Arrow" src={arrowIcon} />
                  </div>
                  <p className="blade-accordion-text">
                    Why is your company not paid immediately? Why do we wait until end of month to invoice? Why does it take so
                    long to produce an invoice? Why is it ok for a customer to mandate payable days of 30, 40, 90 days? Worst-case
                    scenario: the invoice gets disputed, requiring us to restart the payment clock all over again! <br />
                    <br />
                    It doesn&#39;t matter if you are a drilling wells, delivering chemicals or producing hydrocarbons. You can,
                    and should, get paid for value you have delivered immediately.
                  </p>
                </div>
              </div>
              <div
                className={`card-wrapper ${activeFrame === "checkers-checking" ? "active" : ""}`}
                onClick={() => handleFrameClick("checkers-checking")}
              >
              <div className="card">
                <div className="checkers-checking-frame">
                  <div className="checkers-checking-text-wrapper">Checkers checking the checkers</div>
                    <img className="arrow_icon" alt="Arrow" src={arrowIcon} />
                  </div>
                  <p className="blade-accordion-text">
                    To err is human. We all make mistakes. We are only human. Therefore, the industry has built checks into the
                    system to iron out any errors. Both sellers and customers must have multiple levels of approval before payment
                    for an invoice can be approved and paid. There are checkers checking the checkers on all sides of a
                    transaction. <br />
                    <br />
                    Today this is considered a "best practice". When you shine the light of day on it, you just have to ask why?
                    There has to be a better way, and there is. <br />
                  </p>
                </div>
              </div>
              <div
                className={`card-wrapper ${activeFrame === "retail-learning" ? "active" : ""}`}
                onClick={() => handleFrameClick("retail-learning")}
              >
              <div className="card">
                <div className="retail-learning-frame">
                  <div className="retail-learning-text-wrapper">Learning from Retail</div>
                    <img className="arrow_icon" alt="Arrow" src={arrowIcon} />
                  </div>
                  <p className="blade-accordion-text">
                    The better way is to learn from our world of pumping gas for our car. We swipe our credit card, we pump our
                    gas and we leave. We have just agreed to a price. We've agreed on quality. We've agreed to use the pump as a
                    measurement meter, and we've agreed to use our credit card to pay for the transaction. No humans involved. Not
                    an invoice in sight.
                  </p>
                </div>
              </div>
            </div>
            {activeFrame === "get-paid-immediately" && (
              <img className="blade-accordion-image" alt="Get Paid Immediately" src={getPaidImmediatelyImage} />
            )}
            {activeFrame === "checkers-checking" && (
              <img className="blade-accordion-image" alt="Checkers Checking" src={checkersCheckingImage} />
            )}
            {activeFrame === "retail-learning" && (
              <img className="blade-accordion-image" alt="Retail Learning" src={retailLearningImage} />
            )}
          </div>
        </div>
      </div>
      <div className="blade">
        <div className="scrollable-container">
          <div className="grid-wrapper">
            <div className="div-wrapper">
              <p className="blade-text-wrapper">
                Improve your Earnings Per Share
              </p>
            </div>
          </div>
          <div className="conversion-grid">
            <Frame 
              className="conversion-frame" 
              imgSrc={exchangeIcon} 
              imgAlt="Cash conversion" 
              title="Accelerate Cash Conversion"
              text="Leverage your existing supply chain vendor relationships and provide faster payments to vendors, generating
              discounts that you monetize on every payment while automating and streamlining your workflows."
            />
            <Frame 
              className="conversion-frame" 
              imgSrc={paymentsIcon} 
              imgAlt="Payments" 
              title="Straight to the Bottom Line"
              text="New advancements in technology and finance allow you to convert on these opportunities using your existing 
              infrastructure, systems, and contracts. These savings drop straight to your bottom line."
            />
            <Frame 
              className="conversion-frame" 
              imgSrc={monitoringIcon} 
              imgAlt="Monitoring" 
              title="Improve your EPS"
              text="Capture discounts from your supply chain and directly boost your EPS by reducing operating expenses"
            />
          </div>
        </div>
      </div>
      <Footer loginState="default" />
    </div>
  );
};

export default Frontpage;