import BigNumber from "bignumber.js";

export const fromDollaryDoos = (raw, decimals = 2) => {
  if (isNaN(raw)) return '';

  return new BigNumber(raw).dividedBy(10 ** 6).toFixed(decimals);
};

export const toDollaryDoos = (raw) => {
  if (isNaN(raw)) return '';

  return new BigNumber(raw).multipliedBy(10 ** 6).toFixed(0);
};

export const formatNumber = (num)  => {
  const numText = typeof num === 'string' ? num : num.toString();
  const [first, decimals] = numText.split('.');
  const realNum = first.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');

  if (decimals) {
    return `${realNum}.${decimals}`;
  }

  return realNum;
};
