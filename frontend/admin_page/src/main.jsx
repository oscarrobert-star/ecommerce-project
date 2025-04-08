// import React from "react";
// import ReactDOM from "react-dom/client";
// import App from "./App";
// import "bootstrap/dist/css/bootstrap.min.css";

// ReactDOM.createRoot(document.getElementById("root")).render(
//   <React.StrictMode>
//     <App />
//   </React.StrictMode>
// );


// --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import AdminDashboard from "./pages/AdminDashboard";
import OrdersPage from "./pages/Orders";
import ProductsPage from "./pages/Products";
import UsersPage from "./pages/Users";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Customers from "./pages/Customers"; 

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<AdminDashboard />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/customers" element={<Customers />} />
      </Routes>
    </Router>
  </React.StrictMode>
);
