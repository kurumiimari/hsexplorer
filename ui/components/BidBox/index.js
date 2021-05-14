import React, {useCallback} from "react";
import "./bid-box.scss";
import DownloadBob from "./DownloadBob";
import {useBidsByName, usePendingBid, usePendingOpen, useRevealByName, useWallet} from "../../util/bob3";
import {useNameInfo} from "../../util/5pi";
import ConnectToBob from "./ConnectToBob";
import BidPanel from "./BidPanel";
import OpenPanel from "./OpenPanel";
import FindOwnBids from "../FindOwnBids";
import RevealPanel from "./RevealPanel";

export default function BidBox(props) {
  const name = window.location.pathname.split('/')[2];
  const [nameInfo, refreshNameInfo] = useNameInfo(name);
  const [wallet, setWallet] = useWallet();
  const [pendingOpen, refreshPendingOpen] = usePendingOpen(wallet, name);
  const [pendingBid, refreshPendingBid] = usePendingBid(wallet, name);
  const [reveal, refreshReveal] = useRevealByName(wallet, name);

  wallet?.onNewBlock(async (block) => {
    refreshPendingOpen();
    refreshPendingBid();
    refreshReveal();
    refreshNameInfo();
  });

  wallet?.onDisconnect(async () => {
    setWallet();
    refreshPendingOpen();
    refreshPendingBid();
    refreshReveal();
  });

  let child = null;

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
      <OpenPanel
        name={name}
        nameInfo={nameInfo}
        wallet={wallet}
        opening={!!pendingOpen}
        refreshPendingOpen={refreshPendingOpen}
      />
    );
  } else if (nameInfo?.info?.state === 'OPENING') {
    child = (
      <OpenPanel
        name={name}
        nameInfo={nameInfo}
        wallet={wallet}
        refreshPendingOpen={refreshPendingOpen}
        opening
      />
    );
  } else if (nameInfo?.info?.state === 'BIDDING') {
    child = (
      <BidPanel
        name={name}
        wallet={wallet}
        bidding={!!pendingBid}
        refreshPendingBid={refreshPendingBid}
      />
    );
  } else if (nameInfo?.info?.state === 'REVEAL') {
    child = (
      <RevealPanel
        name={name}
        nameInfo={nameInfo}
        wallet={wallet}
        reveal={reveal}
        refreshReveal={refreshReveal}
      />
    );
  }

  return (
    <>
      {child}
      <FindOwnBids wallet={wallet}/>
    </>
  );
}
