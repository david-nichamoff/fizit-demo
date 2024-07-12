import React from "react";
import PropTypes from "prop-types";

import { Button } from "../Button/Button";
import { Logo } from "../Logo/Logo";
import { NavItem } from "../NavItem/NavItem";
import { useNavigate } from "react-router-dom";

import "./Header.css";
import "../StyleGuide/StyleGuide.css";

export const Header = ({ loginState }) => {
  const navigate = useNavigate();

  return (
    <div className={"header"}>
      <div className="container">
        <div className="nav-left">
          <div onClick={() => navigate("/")}>
            <Logo className="logo-instance" logoType="default" />
          </div>
        </div>
        <div className="nav-center">
          <NavItem className="instance-node" status="default" text="How It Works" type="regular" to="/how-it-works" />
          <NavItem className="instance-node" status="default" text="Why Fizit" type="regular" to="/why-fizit" />
          <NavItem className="instance-node" status="default" text="Get a Quote" type="regular" to="/get-a-quote" />
        </div>
        {/*
        <div className="nav-right">
          <div className="grid">
            <NavItem
              className="instance-node"
              divClassName="nav-item-instance"
              status="default"
              text={loginState === "after-login" ? "Contracts" : "Login"}
              type="regular"
              to={loginState === "after-login" ? "/contracts" : "/login"}
            />
            <Button
              className={`instance-node ${loginState === "default" ? "hidden" : ""}`}
              size="small"
              style="primary"
              text={loginState === "after-login" ? "Logout" : "Register"}
              onClick={() => navigate(loginState === "after-login" ? "/logout" : "/register")}
            />
          </div>
        </div>
        */}
      </div>
    </div>
  );
};

Header.propTypes = {
  loginState: PropTypes.oneOf(["after-login", "default"]),
};

export default Header;