import React, { useState } from "react";
import { Container, Form, Button, Tab, Tabs, Alert } from "react-bootstrap";
import { FaGoogle } from "react-icons/fa";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function AuthPage() {
  const [authType, setAuthType] = useState("signin");
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [newPassword, setNewPassword] = useState("");
  const [name, setName] = useState(""); // Used for signup
  const [showNewPasswordField, setShowNewPasswordField] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMessage("");

    const { email, password } = formData;

    try {
      const payload = {
        username: email,
        password: password,
      };

      if (showNewPasswordField && newPassword) {
        payload.new_password = newPassword;
      }

      const response = await axios.post(
        `${import.meta.env.VITE_BASE_URL}/users/login/`,
        payload,
        {
          headers: { "Content-Type": "application/json" },
          withCredentials: true,
        }
      );

      console.log("Login successful:", response.data);
      localStorage.setItem("access_token", response.data.access_token);
      localStorage.setItem("id_token", response.data.id_token);

      navigate("/");
    } catch (error) {
      console.error("Login failed:", error);
      const err = error.response?.data;

      if (err?.challenge === "NEW_PASSWORD_REQUIRED") {
        setShowNewPasswordField(true);
        setFormData({ ...formData, password: "" });
        setErrorMessage("New password required. Please enter a new password.");
      } else {
        setErrorMessage(err?.error || "Login failed. Please try again.");
      }
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setErrorMessage("");

    try {
      await axios.post(`${import.meta.env.VITE_BASE_URL}/users/signup/`, {
        username: formData.email,
        password: formData.password,
        email: formData.email,
        type: "admin", // Hardcoded for admin signup
      });

      alert("Signup successful. Please check your email to confirm.");
      navigate("/confirm-signup");
    } catch (error) {
      console.error("Signup failed:", error);
      setErrorMessage(error.response?.data?.error || "Signup failed");
    }
  };

  const handleSubmit = (e) => {
    if (authType === "signin") {
      handleLogin(e);
    } else {
      handleSignup(e);
    }
  };

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

        <Tabs
          defaultActiveKey="signin"
          activeKey={authType}
          onSelect={(k) => {
            setAuthType(k);
            setErrorMessage("");
            setShowNewPasswordField(false);
          }}
          className="mb-3"
        >
          <Tab eventKey="signin" title="Sign In" />
          <Tab eventKey="signup" title="Sign Up" />
        </Tabs>

        {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}

        <Form onSubmit={handleSubmit}>
          {authType === "signup" && (
            <Form.Group className="mb-3">
              <Form.Label>Full Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter full name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </Form.Group>
          )}

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

          {authType === "signin" && showNewPasswordField && (
            <Form.Group className="mb-3">
              <Form.Label>New Password</Form.Label>
              <Form.Control
                type="password"
                placeholder="Enter new password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </Form.Group>
          )}

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
