import React from "react";
import PropTypes from "prop-types";
import c from "classnames";

export default function Spinner(props) {
  return (
    <svg
      className={c("animate-spin", props.className)}
      width={props.width || 16 + 'px'}
      height={props.height || 16 + 'px'}
      viewBox="0 0 100 100"
      preserveAspectRatio="xMidYMid"
    >
      <circle
        cx="50"
        cy="50"
        fill="none"
        stroke="#fefefe"
        strokeWidth="10"
        r="35"
        strokeDasharray="164.93361431346415 56.97787143782138"
        transform="matrix(1,0,0,1,0,0)"
        style={{
          "transform": 'matrix(1, 0, 0, 1, 0, 0)',
          "animation-play-state":'paused',
        }}
      />
    </svg>
  )
}

Spinner.propTypes = {
  width: PropTypes.number,
  height: PropTypes.number,
  className: PropTypes.string,
};
