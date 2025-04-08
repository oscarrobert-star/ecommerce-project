import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="bg-[#2c3e50] text-white p-4 flex gap-6">
      <Link to="/" className="hover:text-[#e74c3c]">Dashboard</Link>
      <Link to="/orders" className="hover:text-[#e74c3c]">Orders</Link>
      <Link to="/products" className="hover:text-[#e74c3c]">Products</Link>
      <Link to="/users" className="hover:text-[#e74c3c]">Users</Link>
    </nav>
  );
}
