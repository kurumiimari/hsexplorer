import {useState, useEffect} from 'react';
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

  useEffect(() => {
    (async function initBalance() {
      if (!wallet) {
        return;
      }

      setBalance(await wallet.getBalance());
    })();
  }, [wallet]);

  if (!balance) {
    return 0;
  }

  return balance.unconfirmed - balance.lockedUnconfirmed;
}

export function usePendingOpen(wallet, name) {
  const [tx, setTx] = useState(null);

  useEffect(() => {
    (async function initPendingOpen() {
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

    })();
  }, [wallet]);

  return tx;
}
