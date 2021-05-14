import React, {useCallback} from "react";
import "./bid-box.scss";
import DownloadBob from "./DownloadBob";
import {useBidsByName, usePendingBid, usePendingOpen, useWallet} from "../../util/bob3";
import {useNameInfo} from "../../util/5pi";
import ConnectToBob from "./ConnectToBob";
import BiddingPanel from "./BiddingPanel";
import OpeningPanel from "./OpeningPanel";
import FindOwnBids from "../FindOwnBids";

export default function BidBox(props) {
  const name = window.location.pathname.split('/')[2];
  const [nameInfo, refreshNameInfo] = useNameInfo(name);
  const [wallet, setWallet] = useWallet();
  const [pendingOpen, refreshPendingOpen] = usePendingOpen(wallet, name);
  const [pendingBid, refreshPendingBid] = usePendingBid(wallet, name);

  wallet?.onNewBlock(async (block) => {
    refreshPendingOpen();
    refreshPendingBid();
    refreshNameInfo();
  });

  wallet?.onDisconnect(async () => {
    setWallet();
    refreshPendingOpen();
    refreshPendingBid();
    refreshNameInfo();
  });

  let child = <DownloadBob />;

  if (typeof window.bob3 === 'undefined') {
    child = (
      <DownloadBob />
    );
  } else if (!wallet) {
    child = (
      <ConnectToBob setWallet={setWallet} />
    );
  } else if (!nameInfo?.info) {
    child = (
      <OpeningPanel
        name={name}
        nameInfo={nameInfo}
        wallet={wallet}
        opening={!!pendingOpen}
        refreshPendingOpen={refreshPendingOpen}
      />
    );
  } else if (nameInfo?.info?.state === 'OPENING') {
    child = (
      <OpeningPanel
        name={name}
        nameInfo={nameInfo}
        wallet={wallet}
        refreshPendingOpen={refreshPendingOpen}
        opening
      />
    );
  } else if (nameInfo?.info?.state === 'BIDDING') {
    child = (
      <BiddingPanel
        name={name}
        wallet={wallet}
        bidding={!!pendingBid}
        refreshPendingBid={refreshPendingBid}
      />
    );
  } else if (nameInfo?.info?.state === 'REVEAL') {

  }

  return (
    <>
      {child}
      <FindOwnBids wallet={wallet}/>
    </>
  );
}
