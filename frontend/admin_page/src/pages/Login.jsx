import React, { useState } from "react";
import { Container, Form, Button } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e) => {
    e.preventDefault();

    // Simulate successful login (Replace with API call)
    if (email === "admin@example.com" && password === "password") {
      navigate("/"); // Redirect to dashboard
    } else {
      alert("Invalid credentials");
    }
  };

  return (
    <Container className="d-flex flex-column align-items-center justify-content-center vh-100">
      <h2 className="mb-4">Login</h2>
      <Form style={{ width: "300px" }} onSubmit={handleLogin}>
        <Form.Group className="mb-3">
          <Form.Label>Email address</Form.Label>
          <Form.Control 
            type="email" 
            placeholder="Enter email" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
          />
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>Password</Form.Label>
          <Form.Control 
            type="password" 
            placeholder="Password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
          />
        </Form.Group>

        <Button variant="primary" type="submit" className="w-100">
          Login
        </Button>

        {/* Google SSO Login (Just Placeholder for now) */}
        <Button variant="danger" className="w-100 mt-3">
          Login with Google
        </Button>
      </Form>

      <p className="mt-3">
        Don't have an account? <Link to="/signup">Sign Up</Link>
      </p>
    </Container>
  );
}
