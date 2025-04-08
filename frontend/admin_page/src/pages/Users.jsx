import React, { useState } from "react";
import { Container, Table, Form } from "react-bootstrap";
import Sidebar from "../components/Sidebar";

const dummyUsers = [
  { id: 1, name: "John Doe", email: "john@example.com", role: "Admin" },
  { id: 2, name: "Jane Smith", email: "jane@example.com", role: "User" },
  { id: 3, name: "Bob Johnson", email: "bob@example.com", role: "Moderator" },
];

export default function Users() {
  const [search, setSearch] = useState("");

  const filteredUsers = dummyUsers.filter(
    (user) =>
      user.name.toLowerCase().includes(search.toLowerCase()) ||
      user.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="d-flex vh-100" style={{ backgroundColor: "#f3f7ea" }}>
      <Sidebar />
      <Container className="p-4">
        <h1 className="mb-4">Users</h1>

        {/* Search Bar */}
        <Form.Control
          type="text"
          placeholder="Search by name or email..."
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
          <thead style={{ backgroundColor: "#d9e8c2" }}>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.map((user) => (
              <tr
                key={user.id}
                style={{
                  transition: "background-color 0.3s",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor = "#ecf3d5")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = "transparent")
                }
              >
                <td>{user.id}</td>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td
                  style={{
                    color:
                      user.role === "Admin"
                        ? "red"
                        : user.role === "Moderator"
                        ? "blue"
                        : "black",
                    fontWeight: "bold",
                  }}
                >
                  {user.role}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Container>
    </div>
  );
}
