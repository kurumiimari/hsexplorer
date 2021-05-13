import {useState, useEffect} from "react";

const API = 'https://5pi.io/hsd';
function getHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': 'Basic ' + btoa(`x:775f8ca39e1748a7b47ff16ad4b1b9ad`),
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

  useEffect(() => {
    (async function onUseNameInfo() {
      const json = await getNameInfo(name);
      setNameInfo(json.result);
    })()
  }, []);

  return nameInfo;
}
