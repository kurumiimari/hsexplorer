import React, {useEffect} from "react";
import ReactDOM from "react-dom";
import PropTypes from "prop-types";
import {useBidsByName} from "../../util/bob3";

export default function FindOwnBids(props) {
  const name = window.location.pathname.split('/')[2];
  const [bids, refreshBids] = useBidsByName(props.wallet, name);

  useEffect(() => {
    (async function onFindOwnBids() {
      const bidMap = {};

      for (let bid of bids) {
        bidMap[bid.hash] = bid;
      }

      const elements = document.querySelectorAll('[data-tx-hash]');

      for (let el of elements) {
        const bid = bidMap[el.dataset.txHash];
        ReactDOM.render(
          <BidHash wallet={props.wallet} hash={el.dataset.txHash} own={!!bid}/>,
          el
        );
      }
    })();
  }, [bids, props.wallet]);

  return <></>;
}

FindOwnBids.propTypes = {
  wallet: PropTypes.object,
};

function BidHash(props) {
  const {hash, wallet, own} = props;
  return (
    <div className="flex flex-row cursor-default">
      <a href={`/txs/${hash}`} className="text-purple-500">
        {hash.slice(0, 10)}...{hash.slice(-10)}
      </a>
      {
        wallet && own && (
          <div className="flex flex-row items-center bg-purple-700 text-white ml-2 rounded py-0.5 px-1 text-xs font-semibold">
            Your Bid
          </div>
        )
      }
    </div>
  );
}

BidHash.propTypes = {
  own: PropTypes.bool,
  hash: PropTypes.string.isRequired,
  wallet: PropTypes.object,
};
