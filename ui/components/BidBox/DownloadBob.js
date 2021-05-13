import React from "react";

export default function DownloadBob() {
  return (
    <div className="p-8 bg-gray-200 rounded-lg bid-box">
      <div className="text-center text-gray-500 mb-4">
        Use Bob wallet to place a bid.
      </div>
      <a href="https://bobwallet.io" target="_blank"
         className="text-white font-bold block p-4 text-center rounded-md main-cta-button">
        Download Bob
      </a>
    </div>
  );
}
