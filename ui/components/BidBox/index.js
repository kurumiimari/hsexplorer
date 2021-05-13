import React, {useCallback} from "react";
import "./bid-box.scss";
import DownloadBob from "./DownloadBob";
import {useWallet} from "../../util/bob3";
import {useNameInfo} from "../../util/5pi";
import ConnectToBob from "../ConnectToBob";
import BiddingPanel from "./BiddingPanel";

export default function BidBox(props) {
  const name = window.location.pathname.split('/')[2];
  const nameInfo = useNameInfo(name);
  const [wallet, setWallet] = useWallet();

  if (typeof window.bob3 === 'undefined') {
    return <DownloadBob />;
  }

  if (!wallet) {
    return <ConnectToBob setWallet={setWallet} />
  }

  // Name is not opened
  if (!nameInfo?.info) {

  }

  if (nameInfo?.info?.state === 'OPENING') {

  }

  if (nameInfo?.info?.state === 'BIDDING') {
    return <BiddingPanel name={name} wallet={wallet} />;
  }

  if (nameInfo?.info?.state === 'REVEAL') {

  }

  return <DownloadBob />;
}
