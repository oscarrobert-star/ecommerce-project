import React from "react";
import { Container, Form, Button } from "react-bootstrap";
import { Link } from "react-router-dom";

export default function Signup() {
  return (
    <Container className="d-flex flex-column align-items-center justify-content-center vh-100">
      <h2 className="mb-4">Sign Up</h2>
      <Form style={{ width: "300px" }}>
        <Form.Group className="mb-3">
          <Form.Label>Name</Form.Label>
          <Form.Control type="text" placeholder="Enter your name" />
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>Email address</Form.Label>
          <Form.Control type="email" placeholder="Enter email" />
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>Password</Form.Label>
          <Form.Control type="password" placeholder="Password" />
        </Form.Group>

        <Button variant="primary" type="submit" className="w-100">
          Sign Up
        </Button>

        {/* Google SSO Signup */}
        <Button variant="danger" className="w-100 mt-3">
          Sign Up with Google
        </Button>
      </Form>

      <p className="mt-3">
        Already have an account? <Link to="/login">Login</Link>
      </p>
    </Container>
  );
}
