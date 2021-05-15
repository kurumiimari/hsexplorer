import {useState, useEffect, useCallback} from "react";

const API = 'https://5pi.io/hsd';
// const API = 'http://127.0.0.1:15037';
function getHeaders() {
  return {
    // 'Content-Type': 'application/json',
    'Authorization': 'Basic ' + btoa(`x:775f8ca39e1748a7b47ff16ad4b1b9ad`),
    // 'Authorization': 'Basic ' + btoa(`x:9afe245fa32534d07c2a1d2e32a80bc590ac1ed7`),
  };
}

export async function getNameInfo(name) {
  const resp = await fetch(API, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({
      method: 'getnameinfo',
      params: [name],
    }),
  });
  return resp.json();
}

export function useNameInfo(name) {
  const [nameInfo, setNameInfo] = useState();

  const refresh = useCallback(async () => {
    const json = await getNameInfo(name);
    setNameInfo(json.result);
  });

  useEffect(refresh, []);

  return [nameInfo, refresh];
}
