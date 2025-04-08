import React, { useState } from "react";
import { Container, Table, Form } from "react-bootstrap";
import Sidebar from "../components/Sidebar";

const dummyProducts = [
  { id: 201, name: "Laptop", price: "$999.99", stock: "20" },
  { id: 202, name: "Smartphone", price: "$499.50", stock: "35" },
  { id: 203, name: "Headphones", price: "$79.99", stock: "50" },
];

export default function Products() {
  const [search, setSearch] = useState("");

  const filteredProducts = dummyProducts.filter(
    (product) =>
      product.name.toLowerCase().includes(search.toLowerCase()) ||
      product.id.toString().includes(search)
  );

  return (
    <div className="d-flex vh-100" style={{ backgroundColor: "#f8f1f1" }}>
      <Sidebar />
      <Container className="p-4">
        <h1 className="mb-4">Products</h1>

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
                      product.stock > 30
                        ? "green"
                        : product.stock > 10
                        ? "orange"
                        : "red",
                    fontWeight: "bold",
                  }}
                >
                  {product.stock}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Container>
    </div>
  );
}
