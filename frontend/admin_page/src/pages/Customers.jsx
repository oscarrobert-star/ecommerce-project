import React, { useState } from "react";
import { Table, Form, Container } from "react-bootstrap";
import Sidebar from "../components/Sidebar";

const dummyCustomers = [
  {
    id: 1,
    name: "John Doe",
    email: "johndoe@example.com",
    shippingAddress: "123 Main St, New York, NY",
    latestOrder: "#ORD1023",
    status: "Shipped",
  },
  {
    id: 2,
    name: "Jane Smith",
    email: "janesmith@example.com",
    shippingAddress: "456 Elm St, Los Angeles, CA",
    latestOrder: "#ORD1024",
    status: "Processing",
  },
  {
    id: 3,
    name: "Alice Johnson",
    email: "alice@example.com",
    shippingAddress: "789 Oak St, Chicago, IL",
    latestOrder: "#ORD1025",
    status: "Delivered",
  },
];

export default function Customers() {
  const [search, setSearch] = useState("");

  const filteredCustomers = dummyCustomers.filter(
    (customer) =>
      customer.name.toLowerCase().includes(search.toLowerCase()) ||
      customer.email.toLowerCase().includes(search.toLowerCase()) ||
      customer.latestOrder.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="d-flex vh-100" style={{ backgroundColor: "#f3e5f5" }}>
      <Sidebar />
      <Container fluid className="p-4">
        <h2 className="mb-4">Customers Management</h2>

        {/* Search Bar */}
        <Form.Control
          type="text"
          placeholder="Search by name, email, or order ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mb-3"
          style={{
            border: "2px solid #2c3e50",
            borderRadius: "8px",
            backgroundColor: "#ffffff",
          }}
        />

        {/* Customers Table */}
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
          <thead style={{ backgroundColor: "#e1bee7" }}>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Shipping Address</th>
              <th>Latest Order</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredCustomers.map((customer) => (
              <tr
                key={customer.id}
                style={{
                  transition: "background-color 0.3s",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor = "#f8e1ff")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = "transparent")
                }
              >
                <td>{customer.name}</td>
                <td>{customer.email}</td>
                <td>{customer.shippingAddress}</td>
                <td>{customer.latestOrder}</td>
                <td
                  style={{
                    color:
                      customer.status === "Shipped"
                        ? "green"
                        : customer.status === "Processing"
                        ? "orange"
                        : "blue",
                    fontWeight: "bold",
                  }}
                >
                  {customer.status}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Container>
    </div>
  );
}
