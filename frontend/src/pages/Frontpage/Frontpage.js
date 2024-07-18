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
                  FIZIT uses the latest technologies in IoT, AI and blockchain to provide you the fastest possible
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
                className="for-buyers-button"
                divClassName="for-buyers-button"
                riArrowDownLine={riArrowDownLineIcon}
                size="default"
                text="For Buyers"
                onClick={() => navigate("/for-buyers")}
              />
              <ButtonText
                className="for-sellers-button"
                divClassName="for-sellers-button"
                riArrowDownLine={riArrowDownLineIcon}
                size="default"
                text="For Sellers"
                onClick={() => navigate("/for-sellers")}
              />
            </div>
          </div>
          <div className="image-with-chart">
            <img className="person" alt="Person" src={personImage} />
            <img className="chart" alt="Chart" src={chartImage} />
          </div>
        </div>
      </div>
      <Footer loginState="default" />
    </div>
  );
};

export default Frontpage;