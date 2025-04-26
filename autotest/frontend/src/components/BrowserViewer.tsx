import React from "react";

export const BrowserViewer: React.FC = () => (
  <iframe
    title="Live Browser"
    src="http://localhost:7900/?password=marina"
    style={{
      width: "100%",
      height: "100%",
      border: "0",
      borderRadius: "8px",
    }}
  />
);