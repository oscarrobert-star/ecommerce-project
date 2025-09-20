import React, { useState, useEffect } from "react";
import { Container, Table, Form, Button, Spinner } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import axios from "axios";

export default function Products() {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [nextPage, setNextPage] = useState(null);
  const [prevPage, setPrevPage] = useState(null);
  const [isFetching, setIsFetching] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProducts = async () => {
      setIsFetching(true);
      try {
        let url = `${import.meta.env.VITE_API_URL}/products?page=${currentPage}`;

        if (search) {
          url += `&name=${search}`;
        }
        
        const response = await axios.get(url);

        setProducts(response.data.results);
        setNextPage(response.data.next);
        setPrevPage(response.data.previous);
      } catch (error) {
        console.error("Error fetching products:", error);
      } finally {
        setIsFetching(false);
      }
    };

    const handler = setTimeout(() => {
      fetchProducts();
    }, 500);

    return () => {
      clearTimeout(handler);
    };

  }, [currentPage, search]);

  const handleNextPage = () => {
    if (nextPage) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePrevPage = () => {
    if (prevPage) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleViewDetails = (productId) => {
    navigate(`/products/${productId}`);
  };

  const handleSearchChange = (e) => {
    setSearch(e.target.value);
    setCurrentPage(1); 
  };

  return (
    <div className="d-flex vh-100" style={{ backgroundColor: "#f8f1f1" }}>
      <Sidebar />
      <Container className="p-4">
        <div className="d-flex justify-content-between align-items-center mb-4">
          <h1>Products</h1>
          <Button variant="primary" onClick={() => navigate("/products/add")}>
            Add Product
          </Button>
        </div>

        <Form.Control
          type="text"
          placeholder="Search by Product Name..."
          className="mb-3"
          value={search}
          onChange={handleSearchChange}
          style={{
            border: "2px solid #2c3e50",
            borderRadius: "8px",
            backgroundColor: "#ffffff",
          }}
        />

        {isFetching ? (
          <div className="d-flex justify-content-center mt-5">
            <Button variant="primary" disabled>
              <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              Loading...
            </Button>
          </div>
        ) : (
          <Table
            bordered
            hover
            responsive
            className="shadow-sm"
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "8px",
              overflow: "hidden",
            }}
          >
            <thead style={{ backgroundColor: "#f4d1d1" }}>
              <tr>
                <th>Name</th>
                <th>Price</th>
                <th>Stock</th>
                <th>Category</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr
                  key={product.id}
                  style={{
                    transition: "background-color 0.3s",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.backgroundColor = "#fce4e4")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.backgroundColor = "transparent")
                  }
                >
                  <td>{product.name}</td>
                  <td>{product.price}</td>
                  <td
                    style={{
                      color:
                        product.stock_quantity > 30
                          ? "green"
                          : product.stock_quantity > 10
                          ? "orange"
                          : "red",
                      fontWeight: "bold",
                    }}
                  >
                    {product.stock_quantity}
                  </td>
                  <td>{product.category}</td>
                  <td>
                    <Button
                      variant="info"
                      size="sm"
                      onClick={() => handleViewDetails(product.id)}
                    >
                      View/Edit
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
        
        <div className="d-flex justify-content-between mt-4">
          <Button
            variant="secondary"
            onClick={handlePrevPage}
            disabled={!prevPage || isFetching}
          >
            Previous
          </Button>
          <span className="align-self-center">Page {currentPage}</span>
          <Button
            variant="secondary"
            onClick={handleNextPage}
            disabled={!nextPage || isFetching}
          >
            Next
          </Button>
        </div>
      </Container>
    </div>
  );
}