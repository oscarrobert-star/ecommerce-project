import React, { useState, useEffect } from "react";
import { Container, Row, Col, Card, Button, Form } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import "../assets/css/checkoutpage.css";

export default function CheckoutPage() {
    const navigate = useNavigate();
    const [cart, setCart] = useState(JSON.parse(localStorage.getItem("cart")) || []);
    const [name, setName] = useState("");
    const [address, setAddress] = useState("");
    const [email, setEmail] = useState("");
    const [paymentMethod, setPaymentMethod] = useState("credit-card");

    useEffect(() => {
        if (cart.length === 0) {
            navigate("/cart"); // Redirect to cart if cart is empty
        }
    }, [cart, navigate]);

    // Calculate total price
    const calculateTotal = () => {
        return cart.reduce((total, item) => total + item.price * item.quantity, 0).toFixed(2);
    };

    // Handle order submission
    const handleOrderSubmit = (e) => {
        e.preventDefault();
        alert("Order placed successfully!");
        // Clear the cart after successful order
        localStorage.removeItem("cart");
        setCart([]);
        navigate("/"); // Redirect to home after placing the order
    };

    // Back to Cart Handler
    const handleBackToCart = () => {
        navigate("/cart"); // Navigate back to the cart page
    };

    return (
        <Container className="p-4">
            <h2 className="text-center mb-4">Checkout</h2>

            <Row>
                {/* Order Summary */}
                <Col md={6}>
                    <Card className="mb-4">
                        <Card.Body>
                            <h4>Order Summary</h4>
                            {cart.map((product) => (
                                <Row key={product.id} className="mb-3">
                                    <Col xs={8}>
                                        <h5>{product.name}</h5>
                                        <p>Quantity: {product.quantity}</p>
                                    </Col>
                                    <Col xs={4} className="text-right">
                                        <h6>${(product.price * product.quantity).toFixed(2)}</h6>
                                    </Col>
                                </Row>
                            ))}
                            <hr />
                            <Row>
                                <Col xs={8}>
                                    <h5>Total</h5>
                                </Col>
                                <Col xs={4} className="text-right">
                                    <h6>${calculateTotal()}</h6>
                                </Col>
                            </Row>
                        </Card.Body>
                    </Card>
                </Col>

                {/* Shipping Details */}
                <Col md={6}>
                    <Card className="mb-4">
                        <Card.Body>
                            <h4>Shipping Details</h4>
                            <Form onSubmit={handleOrderSubmit}>
                                <Form.Group controlId="formName" className="mb-3">
                                    <Form.Label>Name</Form.Label>
                                    <Form.Control
                                        type="text"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        required
                                    />
                                </Form.Group>

                                <Form.Group controlId="formAddress" className="mb-3">
                                    <Form.Label>Address</Form.Label>
                                    <Form.Control
                                        type="text"
                                        value={address}
                                        onChange={(e) => setAddress(e.target.value)}
                                        required
                                    />
                                </Form.Group>

                                <Form.Group controlId="formEmail" className="mb-3">
                                    <Form.Label>Email</Form.Label>
                                    <Form.Control
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                    />
                                </Form.Group>

                                <Form.Group controlId="formPayment" className="mb-3">
                                    <Form.Label>Payment Method</Form.Label>
                                    <Form.Control
                                        as="select"
                                        value={paymentMethod}
                                        onChange={(e) => setPaymentMethod(e.target.value)}
                                        required
                                    >
                                        <option value="credit-card">Credit Card</option>
                                        <option value="paypal">PayPal</option>
                                    </Form.Control>
                                </Form.Group>

                                <Button variant="success" type="submit" className="w-100 mb-3">
                                    Place Order
                                </Button>
                            </Form>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            {/* Back to Cart Button */}
            <div className="d-flex justify-content-center mt-4">
                <Button variant="secondary" onClick={handleBackToCart}>
                    Back to Cart
                </Button>
            </div>
        </Container>
    );
}
