import React, {useCallback, useState} from "react";
import PropTypes from "prop-types";
import Spinner from "../Spinner";
import moment from 'moment';

export default function OpenPanel(props) {
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const {openPeriodEnd, hoursUntilBidding} = props.nameInfo?.info?.stats || {};

  const openBid = useCallback(async () => {
    setLoading(true);
    try {
      await props.wallet.sendOpen(props.name);
      await props.refreshPendingOpen();
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  }, [props.name, props.wallet]);

  return (
    <div className="p-8 bg-gray-200 rounded-lg bid-box">
      <div className="text-center text-gray-500 mb-4">
        {
          props.opening
            ? `Auction is opening. Check back ${openPeriodEnd ? 'in ' + moment(Date.now() + hoursUntilBidding * 60 * 60 * 1000).fromNow(true) : 'later'} to place a bid.`
            : 'Start the auction process by submitting an open request.'
        }
      </div>
      {error && <div className="text-sm text-red text-center w-full mb-2">{error}</div>}
      <button
        className="text-white font-bold block p-3 text-center rounded-md w-full main-cta-button inline-flex flex-row justify-center items-center"
        onClick={openBid}
        disabled={props.opening || isLoading}
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
            : 'Open Auction'
        }
      </button>
    </div>
  );
}

OpenPanel.propTypes = {
  name: PropTypes.string.isRequired,
  wallet: PropTypes.object,
  refreshPendingOpen: PropTypes.func.isRequired,
  nameInfo: PropTypes.object,
  opening: PropTypes.bool,
};
