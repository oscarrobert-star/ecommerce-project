import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Container, Form, Button, Spinner, Alert, Card } from "react-bootstrap";
import Sidebar from "../components/Sidebar";
import axios from "axios";

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_URL}/products/${id}`);
        setProduct(response.data);
      } catch (err) {
        setError("Failed to load product details.");
        console.error("Error fetching product:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProduct();
  }, [id]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setProduct((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    setImageFile(e.target.files[0]);
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!product) return;

    setIsProcessing(true);
    setError(null);

    try {
      let imageUrl = product.image_url;

      // if new image selected, upload to S3 first
      if (imageFile) {
        const urlResponse = await axios.post(
          `${import.meta.env.VITE_API_URL}/products/get-signed-url`,
          {
            product_id: id,
            fileName: imageFile.name,
            contentType: imageFile.type,
          }
        );
        const { uploadUrl, fileUrl } = urlResponse.data;

        const s3Response = await fetch(uploadUrl, {
          method: "PUT",
          body: imageFile,
          headers: {
            "Content-Type": imageFile.type,
          },
        });

        if (!s3Response.ok) {
          const errorText = await s3Response.text();
          console.error("S3 Error Response:", errorText);
          throw new Error("Failed to upload image to S3.");
        }

        imageUrl = fileUrl; // backend should return the public file URL
      }

      const payload = { ...product, image_url: imageUrl };

      const patchResponse = await axios.patch(
        `${import.meta.env.VITE_API_URL}/products/${id}`,
        payload,
        {
          headers: { "Content-Type": "application/json" },
        }
      );

      setProduct(patchResponse.data); // refresh local state
      setImageFile(null);
    } catch (err) {
      console.error("Update error:", err.response?.data || err.message);
      setError(`Failed to update product: ${err.response?.data?.error || err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <Spinner animation="border" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <Alert variant="danger">{error}</Alert>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <Alert variant="info">Product not found.</Alert>
      </div>
    );
  }

  return (
    <div className="d-flex vh-100" style={{ backgroundColor: "#f8f1f1" }}>
      <Sidebar />
      <Container className="p-4">
        <h1 className="mb-4">Product Details</h1>
        <Button variant="secondary" onClick={() => navigate("/products")}>
          Back to Products
        </Button>

        <Form onSubmit={handleUpdate} className="mt-4">
          <Card className="mb-4">
            <Card.Header>Product Image</Card.Header>
            <Card.Body className="d-flex justify-content-center align-items-center flex-column">
              {product.image_url ? (
                <>
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="img-fluid rounded mb-3"
                    style={{ maxWidth: "300px", maxHeight: "300px" }}
                  />
                  <a href={product.image_url} target="_blank" rel="noopener noreferrer">
                    View Full Image
                  </a>
                </>
              ) : (
                <p>No image available.</p>
              )}
              <Form.Group controlId="formImageUpload" className="mt-3 w-100">
                <Form.Label>Change Image</Form.Label>
                <Form.Control type="file" onChange={handleFileChange} />
              </Form.Group>
            </Card.Body>
          </Card>

          <Form.Group controlId="formProductName" className="mb-3">
            <Form.Label>Product Name</Form.Label>
            <Form.Control
              type="text"
              name="name"
              value={product.name}
              onChange={handleChange}
            />
          </Form.Group>
          <Form.Group controlId="formProductDescription" className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              name="description"
              value={product.description}
              onChange={handleChange}
            />
          </Form.Group>
          <Form.Group controlId="formProductCategory" className="mb-3">
            <Form.Label>Category</Form.Label>
            <Form.Control
              type="text"
              name="category"
              value={product.category}
              onChange={handleChange}
            />
          </Form.Group>
          <Form.Group controlId="formProductPrice" className="mb-3">
            <Form.Label>Price</Form.Label>
            <Form.Control
              type="number"
              step="0.01"
              name="price"
              value={product.price}
              onChange={handleChange}
            />
          </Form.Group>
          <Form.Group controlId="formProductStock" className="mb-3">
            <Form.Label>Stock Quantity</Form.Label>
            <Form.Control
              type="number"
              name="stock_quantity"
              value={product.stock_quantity}
              onChange={handleChange}
            />
          </Form.Group>

          {isProcessing ? (
            <Button variant="success" disabled>
              <Spinner animation="border" size="sm" className="me-2" />
              Saving...
            </Button>
          ) : (
            <Button variant="success" type="submit">
              Save Changes
            </Button>
          )}
        </Form>
      </Container>
    </div>
  );
}
