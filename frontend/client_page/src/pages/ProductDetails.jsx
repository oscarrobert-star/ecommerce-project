import React from "react";
import { useParams } from "react-router-dom";
import { Container, Card, Button } from "react-bootstrap";
import { productsList, bestSellers, newArrivals } from "../data/products"; // Import all products

export default function ProductDetails() {
    const { id } = useParams(); // Get product ID from the URL
    const productId = parseInt(id, 10);

    // Find the product from all lists
    const product = [...productsList, ...bestSellers, ...newArrivals].find(
        (p) => p.id === productId
    );

    if (!product) {
        return <h2 className="text-center mt-5">Product not found</h2>;
    }

    return (
        <Container className="mt-5">
            <Card className="mx-auto shadow" style={{ maxWidth: "600px" }}>
                <Card.Img variant="top" src={product.image} alt={product.name} />
                <Card.Body className="text-center">
                    <Card.Title>{product.name}</Card.Title>
                    <Card.Text>{product.description}</Card.Text>
                    <h4 className="text-primary">${product.price.toFixed(2)}</h4>
                    <Button variant="success">Add to Cart</Button>
                </Card.Body>
            </Card>
        </Container>
    );
}
