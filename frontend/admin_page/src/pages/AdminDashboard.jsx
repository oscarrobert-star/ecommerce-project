import React from "react";
import { Container, Row, Col, Card } from "react-bootstrap";
import Sidebar from "../components/Sidebar";

export default function AdminDashboard() {
  return (
    <div className="d-flex vh-100" style={{ backgroundColor: "#e3f2fd" }}>
      <Sidebar />
      <Container fluid className="p-4">
        <h1 className="mb-4">Dashboard Overview</h1>

        {/* Row 1: Sales & Orders Overview */}
        <Row>
          {[
            { title: "Total Sales", value: "$15,230", color: "text-success" },
            { title: "Total Orders", value: "342", color: "text-primary" },
            { title: "Total Customers", value: "1,245", color: "text-info" },
          ].map((item, idx) => (
            <Col key={idx} md={4}>
              <Card className="mb-3 shadow-sm">
                <Card.Body>
                  <Card.Title>{item.title}</Card.Title>
                  <Card.Text className={`fs-3 fw-bold ${item.color}`}>
                    {item.value}
                  </Card.Text>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>

        {/* Row 2: Orders & Customer Insights */}
        <Row>
          {[
            { title: "Pending Orders", value: "45", color: "text-warning" },
            { title: "Shipped Orders", value: "220", color: "text-success" },
            { title: "Cancelled Orders", value: "12", color: "text-danger" },
          ].map((item, idx) => (
            <Col key={idx} md={4}>
              <Card className="mb-3 shadow-sm">
                <Card.Body>
                  <Card.Title>{item.title}</Card.Title>
                  <Card.Text className={`fs-3 fw-bold ${item.color}`}>
                    {item.value}
                  </Card.Text>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>

        {/* Row 3: Inventory & Performance Metrics */}
        <Row>
          {[
            { title: "Low Stock Alerts", value: "5 Products", color: "text-danger" },
            { title: "New Customers (This Month)", value: "120", color: "text-info" },
            { title: "Average Order Value", value: "$44.50", color: "text-primary" },
          ].map((item, idx) => (
            <Col key={idx} md={4}>
              <Card className="mb-3 shadow-sm">
                <Card.Body>
                  <Card.Title>{item.title}</Card.Title>
                  <Card.Text className={`fs-3 fw-bold ${item.color}`}>
                    {item.value}
                  </Card.Text>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      </Container>
    </div>
  );
}
