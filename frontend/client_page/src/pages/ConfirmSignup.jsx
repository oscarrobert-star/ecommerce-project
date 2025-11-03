import React, { useState } from "react";
import { Container, Form, Button } from "react-bootstrap";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function ConfirmSignup() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");

  const handleConfirm = async (e) => {
    e.preventDefault();
    setError("");

    try {
      await axios.post(`${import.meta.env.VITE_AUTH_API_URL}/users/confirm-signup`, {
        username,
        code
      }, {
        headers: {
          "Content-Type": "application/json",
        }
      });

      alert("Account confirmed successfully!");
      navigate("/login");
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || "Confirmation failed. Please try again.");
    }
  };

  return (
    <Container className="d-flex flex-column align-items-center justify-content-center vh-100">
      <h2 className="mb-4">Confirm Signup</h2>

      <Form style={{ width: "300px" }} onSubmit={handleConfirm}>
        <Form.Group className="mb-3">
          <Form.Label>Username</Form.Label>
          <Form.Control 
            type="text" 
            placeholder="Enter username" 
            value={username} 
            onChange={(e) => setUsername(e.target.value)} 
            required 
          />
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>Confirmation Code</Form.Label>
          <Form.Control 
            type="text" 
            placeholder="Enter code from email" 
            value={code} 
            onChange={(e) => setCode(e.target.value)} 
            required 
          />
        </Form.Group>

        {error && <div className="text-danger mb-3">{error}</div>}

        <Button variant="primary" type="submit" className="w-100">
          Confirm
        </Button>
      </Form>
    </Container>
  );
}
