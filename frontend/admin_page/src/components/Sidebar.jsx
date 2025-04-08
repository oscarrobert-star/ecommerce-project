import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { BarChart, People, Cart, Box } from "react-bootstrap-icons";
import { Button } from "react-bootstrap";

export default function Sidebar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    // Placeholder for clearing auth session (e.g., remove token)
    console.log("User logged out");
    navigate("/login"); // Redirect to login
  };

  return (
    <div className="bg-dark text-white p-4 d-flex flex-column" style={{ width: "250px", height: "100vh" }}>
      <h2 className="mb-4">Admin</h2>
      <nav className="flex-grow-1">
        <Link to="/" className="d-flex align-items-center p-2 text-white text-decoration-none">
          <BarChart size={20} className="me-2" /> Dashboard
        </Link>
        <Link to="/orders" className="d-flex align-items-center p-2 text-white text-decoration-none">
          <Cart size={20} className="me-2" /> Orders
        </Link>
        <Link to="/products" className="d-flex align-items-center p-2 text-white text-decoration-none">
          <Box size={20} className="me-2" /> Products
        </Link>
        <Link to="/users" className="d-flex align-items-center p-2 text-white text-decoration-none">
          <People size={20} className="me-2" /> Users
        </Link>
        <Link to="/customers" className="d-flex align-items-center p-2 text-white text-decoration-none">
          <People size={20} className="me-2" /> Customers
        </Link>

      </nav>

      {/* Logout Button */}
      <Button variant="danger" className="w-100 mt-3" onClick={handleLogout}>
        Logout
      </Button>
    </div>
  );
}
