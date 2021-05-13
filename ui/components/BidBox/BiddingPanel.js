import React, {useCallback} from "react";
import PropTypes from "prop-types";
import {useWalletBalance} from "../../util/bob3";
import {formatNumber, fromDollaryDoos} from "../../util/number";

export default function BiddingPanel(props) {
  const balance = useWalletBalance(props.wallet);
  const placeBid = useCallback(async () => {

  });

  return (
    <div className="p-8 bg-gray-200 rounded-lg bid-box">
      <div className="flex flex-col">
        <div className="flex flex-row text-xs justify-between bid-box__bidding-panel__input-labels">
          <div className="flex flex-row flex-shrink-0 flex-grow-0 bid-box__bidding-panel__input-label">
            Your Bid
          </div>
          <div className="flex flex-row flex-shrink-0 flex-grow-0 bid-box__bidding-panel__spendable">
            Available: {formatNumber(fromDollaryDoos(balance))} HNS
          </div>
        </div>
        <input
          className="py-2 px-4 mt-2 mb-4 border border-transparent focus:outline-none shadow-md rounded-lg"
          type="number"
        />
      </div>
      <div>
        <div className="flex flex-row text-xs justify-between bid-box__bidding-panel__input-labels">
          <div className="flex flex-row flex-shrink-0 flex-grow-0 bid-box__bidding-panel__input-label">
            Your Blind (Optional)
          </div>
        </div>
        <input
          className="py-2 px-4 mt-2 mb-4 w-full border border-transparent focus:outline-none shadow-md rounded-lg"
          type="number"
        />
      </div>
      <button
        className="text-white font-bold block p-4 text-center rounded-md w-full main-cta-button"
        onClick={placeBid}
      >
        Place Bid
      </button>
    </div>
  );
}

BiddingPanel.propTypes = {
  name: PropTypes.string.isRequired,
  wallet: PropTypes.object.isRequired,
};
