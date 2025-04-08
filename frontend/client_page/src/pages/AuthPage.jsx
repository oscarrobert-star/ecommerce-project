import React, { useState } from "react";
import { Container, Form, Button, Tab, Tabs } from "react-bootstrap";
import { FaGoogle } from "react-icons/fa";

export default function AuthPage() {
  const [authType, setAuthType] = useState("signin");
  const [formData, setFormData] = useState({ email: "", password: "" });

  // Handle input changes
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Handle form submission (dummy function for now)
  const handleSubmit = (e) => {
    e.preventDefault();
    console.log(authType.toUpperCase(), formData);
  };

  // Google Login Handler (dummy function for now)
  const handleGoogleLogin = () => {
    console.log("Google Sign In Clicked");
  };

  return (
    <Container
      className="d-flex justify-content-center align-items-center vh-100"
      style={{ backgroundColor: "#f3f4f6" }}
    >
      <div className="p-4 shadow bg-white rounded" style={{ width: "350px" }}>
        <h3 className="text-center mb-3">Welcome</h3>

        {/* Tabs for Sign In / Sign Up */}
        <Tabs
          defaultActiveKey="signin"
          activeKey={authType}
          onSelect={(k) => setAuthType(k)}
          className="mb-3"
        >
          <Tab eventKey="signin" title="Sign In" />
          <Tab eventKey="signup" title="Sign Up" />
        </Tabs>

        {/* Auth Form */}
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Email address</Form.Label>
            <Form.Control
              type="email"
              placeholder="Enter email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Password</Form.Label>
            <Form.Control
              type="password"
              placeholder="Enter password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </Form.Group>

          <Button variant="primary" type="submit" className="w-100">
            {authType === "signin" ? "Sign In" : "Sign Up"}
          </Button>
        </Form>

        <div className="text-center mt-3">
          <Button
            variant="outline-danger"
            className="w-100 d-flex align-items-center justify-content-center"
            onClick={handleGoogleLogin}
          >
            <FaGoogle className="me-2" /> Sign in with Google
          </Button>
        </div>
      </div>
    </Container>
  );
}
