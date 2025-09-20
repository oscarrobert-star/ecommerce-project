import React, { useState, useEffect } from "react";
import { Container, Row, Col, Card, Button, Form } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import "../assets/css/checkoutpage.css";

// Define a constant for your cart items key
const CART_ITEMS_KEY = "cart";
const CART_ID_KEY = "cart_id"; // Also define cart_id key for consistency

export default function CheckoutPage() {
    const navigate = useNavigate();
    // Ensure you're pulling from the correct localStorage key
    const [cart, setCart] = useState(JSON.parse(localStorage.getItem(CART_ITEMS_KEY)) || []);
    const [name, setName] = useState("");
    const [address, setAddress] = useState("");
    const [email, setEmail] = useState("");
    const [paymentMethod, setPaymentMethod] = useState("card");

    useEffect(() => {
        // Redirect to cart if cart is empty
        if (cart.length === 0) {
            navigate("/cart");
        }
    }, [cart, navigate]);

    // Calculate total price
    const calculateTotal = () => {
        // Use parseFloat for item.price as it might be a string from backend/localStorage
        return cart.reduce((total, item) => total + parseFloat(item.price) * item.quantity, 0).toFixed(2);
    };

    // Convert total to integer in kobo (or smallest currency unit)
    const calculateAmountInKobo = () => {
        return Math.round(parseFloat(calculateTotal()) * 100);
    };

    // Prepare item details for backend
    const formatItems = () => {
        return cart.map((item) => ({
            product_id: item.product_id,
            product_name: item.product_name,
            quantity: item.quantity,
            price: item.price.toString(),
        }));
    };

    // Handle order submission
    const handleOrderSubmit = async (e) => {
        e.preventDefault();

        const payload = {
            email: email,
            amount: calculateAmountInKobo(),
            channel: paymentMethod,
            items: formatItems(),
        };

        try {
            const response = await fetch(`${import.meta.env.VITE_BASE_URL}/checkout`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                // If the order couldn't be placed, we should NOT clear the cart.
                throw new Error("Failed to place order or create payment URL.");
            }

            const data = await response.json();

            // --- CRUCIAL CHANGE: Do NOT clear cart HERE. ---
            // The cart should only be cleared AFTER successful payment confirmation
            // (e.g., on a success callback page from the payment gateway).
            // localStorage.removeItem(CART_ITEMS_KEY);
            // localStorage.removeItem(CART_ID_KEY);
            // setCart([]);

            // Redirect to the payment page FIRST
            if (data.data && data.data.authorization_url) {
                window.location.href = data.data.authorization_url;
            } else {
                console.error("Authorization URL not found in response:", data);
                alert("Order placed, but no payment URL returned. Your cart remains in storage.");
                navigate("/"); // Or stay on checkout with an error message
            }
        } catch (error) {
            console.error("Error placing order:", error);
            alert("There was an error placing your order. Please try again. Your cart was not cleared.");
        }
    };

    // Back to Cart Handler
    const handleBackToCart = () => {
        navigate("/cart");
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
                            {cart.map((product, index) => (
                                <Row key={product.product_id || index} className="mb-3">
                                    <Col xs={8}>
                                        <h5>{product.product_name || "Unknown Product"}</h5>
                                        <p>Quantity: {product.quantity}</p>
                                    </Col>
                                    <Col xs={4} className="text-right">
                                        <h6>${(parseFloat(product.price) * product.quantity).toFixed(2)}</h6>
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
                                    <Form.Select
                                        value={paymentMethod}
                                        onChange={(e) => setPaymentMethod(e.target.value)}
                                        required
                                    >
                                        <option value="card">Card</option>
                                        <option value="mobile_money">Mobile Money</option>
                                    </Form.Select>
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