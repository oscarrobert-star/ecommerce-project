import React, { useState } from "react";
import { Container, Table, Form } from "react-bootstrap";
import Sidebar from "../components/Sidebar";

const dummyOrders = [
  { id: 101, customer: "John Doe", total: "$120.00", status: "Shipped" },
  { id: 102, customer: "Jane Smith", total: "$95.50", status: "Processing" },
  { id: 103, customer: "Alice Brown", total: "$210.75", status: "Delivered" },
];

export default function Orders() {
  const [search, setSearch] = useState("");

  const filteredOrders = dummyOrders.filter(
    (order) =>
      order.customer.toLowerCase().includes(search.toLowerCase()) ||
      order.id.toString().includes(search)
  );

  return (
    <div className="d-flex vh-100" style={{ backgroundColor: "#e8f5e9" }}>
      <Sidebar />
      <Container className="p-4">
        <h1 className="mb-4">Orders</h1>

        {/* Search Bar */}
        <Form.Control
          type="text"
          placeholder="Search by Order ID or Customer Name..."
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
          <thead style={{ backgroundColor: "#e3f2fd" }}>
            <tr>
              <th>Order ID</th>
              <th>Customer</th>
              <th>Total</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredOrders.map((order) => (
              <tr
                key={order.id}
                style={{
                  transition: "background-color 0.3s",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor = "#f0f8ff")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = "transparent")
                }
              >
                <td>{order.id}</td>
                <td>{order.customer}</td>
                <td>{order.total}</td>
                <td
                  style={{
                    color:
                      order.status === "Shipped"
                        ? "green"
                        : order.status === "Processing"
                        ? "orange"
                        : "blue",
                    fontWeight: "bold",
                  }}
                >
                  {order.status}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Container>
    </div>
  );
}
