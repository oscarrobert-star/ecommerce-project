import React, { useState } from "react";
import { Container, Form, Button } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showNewPasswordField, setShowNewPasswordField] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMessage("");

    try {
      const payload = {
        username: email,
        password: password,
      };

      if (showNewPasswordField && newPassword) {
        payload.new_password = newPassword;
      }

      const response = await axios.post(`${import.meta.env.VITE_AUTH_API_URL}/users/login/`, payload, {
        headers: {
          "Content-Type": "application/json"
        },
        withCredentials: true,
      });

      console.log("Login successful:", response.data);

      localStorage.setItem("access_token", response.data.access_token);
      localStorage.setItem("id_token", response.data.id_token);

      navigate("/"); // Redirect to homepage
    } catch (error) {
      console.error("Login failed:", error);

      const err = error.response?.data;
      if (err?.challenge === "NEW_PASSWORD_REQUIRED") {
        setShowNewPasswordField(true);
        setPassword("");  // Clear old password field
        setErrorMessage("New password required. Please enter a new password.");
      } else {
        setErrorMessage(err?.error || "Login failed. Please try again.");
      }
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
            placeholder={showNewPasswordField ? "Old password cleared" : "Password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={showNewPasswordField} // Optional: disable old password field after challenge
          />
        </Form.Group>

        {showNewPasswordField && (
          <Form.Group className="mb-3">
            <Form.Label>New Password</Form.Label>
            <Form.Control
              type="password"
              placeholder="Enter new password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
          </Form.Group>
        )}

        {errorMessage && <p style={{ color: "red" }}>{errorMessage}</p>}

        <Button variant="primary" type="submit" className="w-100">
          {showNewPasswordField ? "Set New Password" : "Login"}
        </Button>

        {/* Google SSO Login (Placeholder) */}
        <Button variant="danger" className="w-100 mt-3" disabled>
          Login with Google
        </Button>
      </Form>

      <p className="mt-3">
        Don't have an account? <Link to="/signup">Sign Up</Link>
      </p>
    </Container>
  );
}
