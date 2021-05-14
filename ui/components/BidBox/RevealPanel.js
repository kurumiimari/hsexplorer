import React, {useCallback, useState} from "react";
import PropTypes from "prop-types";
import moment from "moment";
import Spinner from "../Spinner";
import {formatNumber, fromDollaryDoos} from "../../util/number";

export default function RevealPanel(props) {
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const hoursUntilClose = props.nameInfo?.info?.stats?.hoursUntilClose;
  const [revealable, totals] = props.reveal
      ? props.reveal.inputs?.reduce(([sum, count], input) => {
        if (input.coin.covenant.action === 'BID') {
          sum += input.coin.value;
          count++;
        }
        return [sum, count];
      }, [0, 0])
      : [0, 0];

  const revealBid = useCallback(async () => {
    try {
      setLoading(true);
      await props.wallet.sendReveal(props.name);
      props.refreshReveal()
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  }, [props.wallet, props.name]);

  return (
    <div className="p-8 bg-gray-200 rounded-lg bid-box">
      <div className="text-center text-gray-500 mb-4">
        {
          !totals
            ? 'You have no bids to reveal.'
            : totals < 2
            ? 'You have 1 bid to reveal'
            : `You have ${totals} bids to reveal.`
        }
      </div>
      {
        !!totals && (
          <div className="text-center text-yellow-700 mb-4 bg-yellow-100 m-4 py-2 px-4 text-sm rounded">
            {`You will lose ${formatNumber(fromDollaryDoos(revealable))} HNS if you don't reveal in ${moment(Date.now() + hoursUntilClose * 60 * 60 * 1000).fromNow(true)}.`}
          </div>
        )
      }
      {error && <div className="text-sm text-red text-center w-full mb-2">{error}</div>}
      {
        totals > 0 && (
          <button
            className="text-white font-bold block p-2 text-center rounded-md w-full main-cta-button inline-flex flex-row justify-center items-center"
            onClick={revealBid}
            disabled={isLoading}
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
                : 'Submit Reveal'
            }
          </button>
        )
      }
    </div>
  )
}

RevealPanel.propTypes = {
  name: PropTypes.string.isRequired,
  refreshReveal: PropTypes.func.isRequired,
  nameInfo: PropTypes.object,
  wallet: PropTypes.object,
  reveal: PropTypes.object,
};
