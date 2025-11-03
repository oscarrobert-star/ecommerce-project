import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
    Container,
    Spinner,
    Alert,
    Button,
    Card,
    Row,
    Col,
    ListGroup,
} from "react-bootstrap";

const OrderConfirmationPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const queryParams = new URLSearchParams(location.search);
    const reference = queryParams.get("reference");

    const [loading, setLoading] = useState(true);
    const [status, setStatus] = useState("");
    const [message, setMessage] = useState("");
    const [order, setOrder] = useState(null);

    useEffect(() => {
        if (!reference) {
            setMessage("Missing order reference.");
            setStatus("failed");
            setLoading(false);
            return;
        }

        const fetchOrderStatus = async () => {
            try {
                const response = await fetch(
                    `${import.meta.env.VITE_BASE_URL}/orders/status/${reference}`
                );

                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error("Order not found.");
                    } else {
                        throw new Error("Failed to fetch order status.");
                    }
                }

                const data = await response.json();
                setOrder(data);
                setStatus("success");
                setMessage("Your order has been confirmed!");

                // Clear cart data from localStorage
                localStorage.removeItem("cart");
                localStorage.removeItem("cart_id");
            } catch (error) {
                setStatus("failed");
                setMessage(error.message || "Failed to fetch order status.");
            } finally {
                setLoading(false);
            }
        };

        fetchOrderStatus();
    }, [reference]);

    const handleContinueShopping = () => {
        navigate("/");
    };

    return (
        <Container className="mt-5">
            {loading ? (
                <div className="text-center">
                    <Spinner animation="border" role="status" />
                    <p className="mt-3">{message || "Loading..."}</p>
                </div>
            ) : (
                <>
                    {status === "success" && (
                        <Alert variant="success" className="text-center">
                            <h4>Order Confirmed!</h4>
                            <p>{message}</p>
                        </Alert>
                    )}

                    {status === "failed" && (
                        <Alert variant="danger" className="text-center">
                            <h4>Order Failed</h4>
                            <p>{message}</p>
                            <Button variant="danger" onClick={() => navigate("/cart")}>
                                Return to Cart
                            </Button>
                        </Alert>
                    )}

                    {order && status === "success" && (
                        <Card className="mt-4">
                            <Card.Header as="h5">Order Details</Card.Header>
                            <Card.Body>
                                <Row className="mb-2">
                                    <Col md={6}><strong>Order ID:</strong> {order.id}</Col>
                                    <Col md={6}><strong>Reference:</strong> {order.payment_reference}</Col>
                                </Row>
                                <Row className="mb-2">
                                    <Col md={6}>
                                        <strong>Payment Status:</strong>{" "}
                                        <span className={`badge ${
                                            order.payment_status === "paid" || order.payment_status === "completed"
                                                ? "bg-success"
                                                : order.payment_status === "pending"
                                                ? "bg-warning text-dark"
                                                : "bg-danger"
                                        }`}>
                                            {order.payment_status?.toUpperCase() || "UNKNOWN"}
                                        </span>
                                    </Col>
                                    <Col md={6}>
                                        <strong>Shipping Status:</strong>{" "}
                                        <span className={`badge ${
                                            order.shipping_status === "pending"
                                                ? "bg-warning text-dark"
                                                : order.shipping_status === "shipped"
                                                ? "bg-success"
                                                : "bg-secondary"
                                        }`}>
                                            {order.shipping_status?.toUpperCase() || "UNKNOWN"}
                                        </span>
                                    </Col>
                                </Row>
                                <Row className="mb-2">
                                    <Col md={6}>
                                        <strong>Total:</strong> $
                                        {order.total_amount ? Number(order.total_amount).toFixed(2) : "0.00"}
                                    </Col>
                                    <Col md={6}>
                                        <strong>Created:</strong> {new Date(order.created_at).toLocaleString()}
                                    </Col>
                                </Row>

                                <h6 className="mt-4">Items:</h6>
                                <ListGroup>
                                    {(order.items || []).map((item, i) => (
                                        <ListGroup.Item key={item.id || i}>
                                            <Row>
                                                <Col>{item.product_name}</Col>
                                                <Col className="text-end">
                                                    {item.quantity} x ${Number(item.price).toFixed(2)} = $
                                                    {(Number(item.quantity) * Number(item.price)).toFixed(2)}
                                                </Col>
                                            </Row>
                                        </ListGroup.Item>
                                    ))}
                                </ListGroup>
                            </Card.Body>
                        </Card>
                    )}

                    <div className="text-center mt-4">
                        <Button variant="primary" onClick={handleContinueShopping}>
                            Continue Shopping
                        </Button>
                    </div>
                </>
            )}
        </Container>
    );
};

export default OrderConfirmationPage;
