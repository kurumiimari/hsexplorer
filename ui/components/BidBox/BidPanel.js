import React, {useCallback, useState} from "react";
import PropTypes from "prop-types";
import {useWalletBalance} from "../../util/bob3";
import {formatNumber, fromDollaryDoos} from "../../util/number";
import Spinner from "../Spinner";

export default function BidPanel(props) {
  const [bid, setBid] = useState('');
  const [blind, setBlind] = useState();
  const [isLoading, setLoading] = useState(false);
  const [balance] = useWalletBalance(props.wallet);
  const [error, setError] = useState('');

  const placeBid = useCallback(async () => {
    setLoading(true);
    try {
      await props.wallet.sendBid(props.name, bid, (blind || 0) + bid);
      setBid('');
      setBlind('');
      props.refreshPendingBid();
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  }, [bid, blind, props.name, props.wallet]);

  const setAmount = useCallback(async (e, update) => {
    if (e.target.value === '') return update('');
    update(+e.target.value);
  }, []);

  return (
    <div className="p-8 bg-gray-200 rounded-lg bid-box">
      <div className="flex flex-col">
        <div className="flex flex-row text-xs justify-between font-semibold text-label-gray">
          <div className="flex flex-row flex-shrink-0 flex-grow-0">
            Your Bid
          </div>
          <div className="flex flex-row flex-shrink-0 flex-grow-0">
            Available: {formatNumber(fromDollaryDoos(balance))} HNS
          </div>
        </div>
        <input
          className="py-2 px-4 mt-2 mb-4 border border-transparent focus:outline-none shadow-md rounded-lg"
          type="number"
          onChange={e => setAmount(e, setBid)}
          disabled={props.bidding}
          value={bid}
        />
      </div>
      <div>
        <div className="flex flex-row text-xs justify-between font-semibold text-label-gray">
          <div className="flex flex-row flex-shrink-0 flex-grow-0">
            Your Blind (Optional)
          </div>
        </div>
        <input
          className="py-2 px-4 mt-2 mb-4 w-full border border-transparent focus:outline-none shadow-md rounded-lg"
          type="number"
          onChange={e => setAmount(e, setBlind)}
          disabled={props.bidding}
          value={blind}
        />
      </div>
      {error && <div className="text-sm text-red text-center w-full mb-2">{error}</div>}
      <button
        className="text-white font-bold block p-2 text-center rounded-md w-full main-cta-button inline-flex flex-row justify-center items-center"
        disabled={props.bidding || bid === '' || isLoading}
        onClick={placeBid}
      >
        {
          isLoading
            ? (
              <Spinner
                className="mr-4"
                width={32}
                height={32}
              />
            )
            : props.bidding ? 'Placing bid...' : 'Place bid'
        }
      </button>
    </div>
  );
}

BidPanel.propTypes = {
  name: PropTypes.string.isRequired,
  wallet: PropTypes.object.isRequired,
  bidding: PropTypes.bool,
  refreshPendingBid: PropTypes.func.isRequired,
};
