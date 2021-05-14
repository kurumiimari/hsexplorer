import {useState, useEffect, useCallback} from 'react';
import {getTXAction, getTXNameHash} from "./tx";

export function useWallet() {
  const [wallet, setWallet] = useState(null);

  useEffect(() => {
    (async function initWallet() {
      if (typeof window.bob3 === 'undefined') {
        return;
      }

      const isLocked = await bob3.isLocked();

      if (!isLocked) {
        setWallet(await bob3.connect());
      }
    })();
  }, []);

  return [wallet, setWallet];
}

export function useWalletBalance(wallet) {
  const [balance, setBalance] = useState(null);

  const refresh = useCallback(async () => {
    if (!wallet) {
      return;
    }

    setBalance(await wallet.getBalance());
  }, [wallet]);

  useEffect(refresh, [wallet]);

  if (!balance) {
    return [0, refresh];
  }

  return [balance.unconfirmed - balance.lockedUnconfirmed, refresh];
}

export function usePendingOpen(wallet, name) {
  const [tx, setTx] = useState(null);

  const refresh = useCallback(async () => {
    setTx(null);

    if (!wallet) {
      return;
    }

    const targetNameHash = await wallet.hashName(name);
    const pendingTXs = await wallet.getPending();


    for (let tx of pendingTXs) {
      const nameHash = getTXNameHash(tx);
      const action = getTXAction(tx);

      if (action === 'OPEN' && nameHash === targetNameHash) {
        setTx(tx);
        return;
      }
    }
  }, [wallet]);

  useEffect(refresh, [wallet]);

  return [tx, refresh];
}

export function usePendingBid(wallet, name) {
  const [tx, setTx] = useState(null);

  const refresh = useCallback(async () => {
    setTx(null);

    if (!wallet) {
      return;
    }

    const targetNameHash = await wallet.hashName(name);
    const pendingTXs = await wallet.getPending();

    for (let tx of pendingTXs) {
      const nameHash = getTXNameHash(tx);
      const action = getTXAction(tx);

      if (action === 'BID' && nameHash === targetNameHash) {
        setTx(tx);
        return;
      }
    }
  }, [wallet]);

  useEffect(refresh, [wallet]);

  return [tx, refresh];
}

export function useBidsByName(wallet, name) {
  const [bids, setBids] = useState([]);

  const refresh = useCallback(async () => {
    setBids([]);

    if (!wallet) {
      return;
    }

    setBids(await wallet.getBidsByName(name));
  }, [wallet]);

  useEffect(refresh, [wallet]);

  return [bids, refresh];
}
