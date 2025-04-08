import React from "react";
import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div style={{ padding: "20px", textAlign: "center" }}>
      <h1>404 - Page Not Found</h1>
      <Link to="/">Go Back Home</Link>
    </div>
  );
}
