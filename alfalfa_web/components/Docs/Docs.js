import React from "react";

export const Docs = () => {
  return (
    <div style={{ display: "flex", flex: 1 }}>
      <iframe src="/redoc" style={{ border: 0, width: "100vw" }}></iframe>
    </div>
  );
};
