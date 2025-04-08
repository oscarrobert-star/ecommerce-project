import React, { useState } from "react";
import { Form, Button, Container } from "react-bootstrap";
import axios from "axios";
import Sidebar from "../components/Sidebar";
import { useNavigate } from "react-router-dom";

export default function AddProduct() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    price: "",
    stock_quantity: "",
    category: "",
    image_url: "",
  });

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${import.meta.env.VITE_API_URL}/products/`, formData);
      alert("Product added!");
      navigate("/products");
    } catch (err) {
      console.error(err);
      alert("Failed to add product");
    }
  };

  return (
    <div className="d-flex vh-100" style={{ backgroundColor: "#f8f1f1" }}>
      <Sidebar />
      <Container className="p-4">
        <h2 className="mb-4">Add Product</h2>
        <Form onSubmit={handleSubmit}>
          {["name", "description", "price", "stock_quantity", "category", "image_url"].map((field) => (
            <Form.Group className="mb-3" controlId={field} key={field}>
              <Form.Label>{field.replace("_", " ").toUpperCase()}</Form.Label>
              <Form.Control
                type={field.includes("price") || field.includes("stock") ? "number" : "text"}
                name={field}
                value={formData[field]}
                onChange={handleChange}
                required={field !== "image_url"}
              />
            </Form.Group>
          ))}
          <Button type="submit" variant="success">
            Add Product
          </Button>
        </Form>
      </Container>
    </div>
  );
}
