import React, {useCallback, useState} from "react";
import PropTypes from "prop-types";
import "../../util/base.scss";
import Spinner from "../Spinner";

export default function ConnectToBob(props) {
  const [connecting, setConnecting] = useState();
  const connectToBob = useCallback(async () => {
    setConnecting(true);
    try {
      const w = await bob3.connect();
      props.setWallet(w);
    } catch(e) {
      throw e;
    } finally {
      setConnecting(false);
    }
  }, []);

  return (
    <div className="p-8 bg-gray-200 rounded-lg bid-box">
      <div className="text-center text-gray-500 mb-4">
        You must be connected to a wallet in order to place a bid.
      </div>
      <button
        className="text-white font-bold block p-2 text-center rounded-md w-full main-cta-button inline-flex flex-row justify-center items-center"
        onClick={connectToBob}
      >
        {
          connecting
            ? (
              <Spinner
                className="mr-4"
                width={32}
                height={32}
              />
            )
            : 'Connect to a wallet'
        }
      </button>
    </div>
  )
}

ConnectToBob.propTypes = {
  setWallet: PropTypes.func.isRequired,
};
