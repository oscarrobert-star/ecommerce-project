import React, { useState } from "react";
import { Container, Form, Button, Spinner, ProgressBar } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import axios from "axios";

export default function AddProduct() {
  const navigate = useNavigate();
  const [productDetails, setProductDetails] = useState({
    name: "",
    description: "",
    category: "",
    price: "",
    stock_quantity: "",
  });
  const [imageFile, setImageFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleDetailsChange = (e) => {
    const { name, value } = e.target;
    setProductDetails({ ...productDetails, [name]: value });
  };

  const handleFileChange = (e) => {
    setImageFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsProcessing(true);

    try {
      const createResponse = await axios.post(
        `${import.meta.env.VITE_API_URL}/products`,
        {
          ...productDetails,
          price: parseFloat(productDetails.price),
          stock_quantity: parseInt(productDetails.stock_quantity),
        }
      );
      const { id } = createResponse.data;

      if (imageFile) {
        const urlResponse = await axios.post(
          `${import.meta.env.VITE_API_URL}/products/get-signed-url`,
          {
            product_id: id,
            fileName: imageFile.name,
            contentType: imageFile.type,
          }
        );
        const { uploadUrl } = urlResponse.data;

        // Use XMLHttpRequest to track upload progress
        const xhr = new XMLHttpRequest();
        xhr.open('PUT', uploadUrl, true);
        xhr.setRequestHeader('Content-Type', imageFile.type);

        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            setUploadProgress(progress);
          }
        });

        await new Promise((resolve, reject) => {
          xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve();
            } else {
              reject(new Error(`S3 upload failed with status ${xhr.status}`));
            }
          };
          xhr.onerror = () => {
            reject(new Error('XMLHttpRequest failed.'));
          };
          xhr.send(imageFile);
        });

        console.log("S3 upload successful!");
      }

      console.log("Product and image uploaded successfully!");
      navigate("/products");

    } catch (error) {
      console.error("Full error details:", error);
      alert("Failed to save product. Check console for details.");
    } finally {
      setIsProcessing(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="d-flex vh-100" style={{ backgroundColor: "#f8f1f1" }}>
      <Sidebar />
      <Container className="p-4">
        <h1 className="mb-4">Add Product</h1>
        <Form onSubmit={handleSubmit}>
          <div className="mb-4">
            <h2>Product Details</h2>
            <Form.Group controlId="formProductName" className="mb-3">
              <Form.Label>Product Name</Form.Label>
              <Form.Control
                type="text"
                name="name"
                value={productDetails.name}
                onChange={handleDetailsChange}
                required
              />
            </Form.Group>
            <Form.Group controlId="formProductDescription" className="mb-3">
              <Form.Label>Description</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                name="description"
                value={productDetails.description}
                onChange={handleDetailsChange}
                required
              />
            </Form.Group>
            <Form.Group controlId="formProductCategory" className="mb-3">
              <Form.Label>Category</Form.Label>
              <Form.Control
                type="text"
                name="category"
                value={productDetails.category}
                onChange={handleDetailsChange}
                required
              />
            </Form.Group>
            <Form.Group controlId="formProductPrice" className="mb-3">
              <Form.Label>Price</Form.Label>
              <Form.Control
                type="number"
                name="price"
                value={productDetails.price}
                onChange={handleDetailsChange}
                required
              />
            </Form.Group>
            <Form.Group controlId="formProductStock" className="mb-3">
              <Form.Label>Stock Quantity</Form.Label>
              <Form.Control
                type="number"
                name="stock_quantity"
                value={productDetails.stock_quantity}
                onChange={handleDetailsChange}
                required
              />
            </Form.Group>
            <Form.Group controlId="formImageUpload" className="mb-3">
              <Form.Label>Select Image</Form.Label>
              <Form.Control type="file" onChange={handleFileChange} />
            </Form.Group>
          </div>

          {isProcessing && (
            <div className="mb-3">
              <p>Saving and Uploading...</p>
              <ProgressBar
                animated
                now={uploadProgress}
                label={`${uploadProgress}%`}
              />
            </div>
          )}

          <Button variant="primary" type="submit" disabled={isProcessing}>
            {isProcessing ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                />
                <span className="ms-2">Saving...</span>
              </>
            ) : (
              "Save Product"
            )}
          </Button>
        </Form>
      </Container>
    </div>
  );
}