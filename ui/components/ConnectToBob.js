import React, {useCallback} from "react";
import PropTypes from "prop-types";

export default function ConnectToBob(props) {
  const connectToBob = useCallback(async () => {
    const w = await bob3.connect();
    props.setWallet(w);
  }, []);

  return (
    <div className="p-8 bg-gray-200 rounded-lg bid-box">
      <div className="text-center text-gray-500 mb-4">
        You must be connected to a wallet in order to place a bid.
      </div>
      <button
        className="text-white font-bold block p-4 text-center rounded-md w-full main-cta-button"
        onClick={connectToBob}
      >
        Connect to a wallet
      </button>
    </div>
  )
}

ConnectToBob.propTypes = {
  setWallet: PropTypes.func.isRequired,
};
