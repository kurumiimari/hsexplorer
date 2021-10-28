import React from "react";
import "./nav-more-btn.scss";

export default function NavMoreButton() {
  return (
    <div
      className="nav-more-btn"
    >
      <div className="nav-more-btn__btn">More</div>
      <div className="nav-more-btn__menu">
        <a href="https://bobwallet.io" target="_blank" className="nav-more-btn__menu-row">
          <div className="nav-more-btn__menu-row__icon">
            <img src="/static/images/bob-black.png" />
          </div>
          <div>bobwallet.io</div>
        </a>
        <a href="https://shakedex.com" target="_blank"  className="nav-more-btn__menu-row">
          <div className="nav-more-btn__menu-row__icon">
            <img src="/static/images/shakedex.svg" />
          </div>
          <div>shakedex.com</div>
        </a>
        <a href="https://shells.com" target="_blank"  className="nav-more-btn__menu-row">
          <div className="nav-more-btn__menu-row__icon">
            <img src="/static/images/shells-logo.ico" />
          </div>
          <div>shells.com</div>
        </a>
      </div>
    </div>
  );
}
