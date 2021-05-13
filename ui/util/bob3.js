import {useState, useEffect} from 'react';

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
  }, []);

  if (!balance) {
    return 0;
  }

  return balance.unconfirmed - balance.lockedUnconfirmed;
}
