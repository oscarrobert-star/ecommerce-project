import React, { useState, useEffect } from "react";
import { Container, Table, Form, Button } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import axios from "axios";

export default function Products() {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  // Fetch products from backend on component mount
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_URL}/products/`);
        setProducts(response.data);  // Assuming the backend returns an array of products
      } catch (error) {
        console.error("Error fetching products:", error);
      }
    };

    fetchProducts();
  }, []);  // Empty dependency array means this runs only once when the component mounts

  // Filter products based on search input
  const filteredProducts = products.filter(
    (product) =>
      product.name.toLowerCase().includes(search.toLowerCase()) ||
      product.id.toString().includes(search)
  );

  return (
    <div className="d-flex vh-100" style={{ backgroundColor: "#f8f1f1" }}>
      <Sidebar />
      <Container className="p-4">
        <div className="d-flex justify-content-between align-items-center mb-4">
          <h1>Products</h1>
          {/* Add Product Button */}
          <Button
            variant="primary"
            onClick={() => navigate("/products/add")}
          >
            Add Product
          </Button>
        </div>

        {/* Search Bar */}
        <Form.Control
          type="text"
          placeholder="Search by Product ID or Name..."
          className="mb-3"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            border: "2px solid #2c3e50",
            borderRadius: "8px",
            backgroundColor: "#ffffff",
          }}
        />

        {/* Styled Table */}
        <Table
          bordered
          hover
          responsive
          className="shadow-sm"
          style={{
            backgroundColor: "#ffffff",
            borderRadius: "8px",
            overflow: "hidden",
          }}
        >
          <thead style={{ backgroundColor: "#f4d1d1" }}>
            <tr>
              <th>Product ID</th>
              <th>Name</th>
              <th>Price</th>
              <th>Stock</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map((product) => (
              <tr
                key={product.id}
                style={{
                  transition: "background-color 0.3s",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor = "#fce4e4")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = "transparent")
                }
              >
                <td>{product.id}</td>
                <td>{product.name}</td>
                <td>{product.price}</td>
                <td
                  style={{
                    color:
                      product.stock_quantity > 30
                        ? "green"
                        : product.stock_quantity > 10
                        ? "orange"
                        : "red",
                    fontWeight: "bold",
                  }}
                >
                  {product.stock_quantity}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Container>
    </div>
  );
}
