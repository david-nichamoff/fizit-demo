import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/Button/Button";
import { ButtonText } from "../../components/ButtonText/ButtonText";
import { Footer } from "../../components/Footer/Footer";
import { Header } from "../../components/Header/Header";

import riArrowDownLineIcon from "../../../static/assets/icon/ri_arrow-down-line.png";

import personImage from "../../../static/assets/image/man.png";
import chartImage from "../../../static/assets/image/cash_chart.png";

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
                <p className="hero-heading">It's Your Money and Timing is Everything</p>
                <p className="hero-text">
                FIZIT enables you to optimize cash flow. Leveraging the latest technologies, FIZIT can help you in ways banks and factoring companies can’t meet.
                </p>
              </div>
            </div>
            <div className="hero-quote-grid">
              <Button
                className="quote-button"
                size="default"
                style="primary"
                text="Let's Talk"
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